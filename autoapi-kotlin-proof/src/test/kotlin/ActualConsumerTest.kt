package com.embabel.autoapi

import com.embabel.agent.config.models.docker.DockerConnectionProperties
import com.embabel.agent.config.models.docker.DockerLocalModelsConfig
import com.embabel.agent.config.models.docker.DockerRetryProperties
import com.embabel.agent.openai.OpenAiCompatibleModelFactory
import com.embabel.agent.spi.support.springai.SpringAiLlmService
import com.embabel.common.ai.model.ConfigurableModelProviderProperties
import com.embabel.common.ai.model.PricingModel
import com.embabel.common.ai.model.SpringAiEmbeddingService
import com.embabel.common.util.ObjectProviders
import com.sun.net.httpserver.HttpServer
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.Timeout
import org.springframework.beans.factory.support.DefaultListableBeanFactory
import java.net.InetSocketAddress
import java.nio.charset.StandardCharsets.UTF_8
import java.util.concurrent.CopyOnWriteArrayList

/** Runs unchanged customer entry points with real Spring AI clients, against loopback only.
 * No replacement customer implementation or SDK stub is part of this fixture.
 */
@Timeout(30)
class ActualConsumerTest {
    private data class Request(val path: String, val authorization: String?, val header: String?, val body: String)

    private class Loopback : AutoCloseable {
        val requests = CopyOnWriteArrayList<Request>()
        private val server = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
        val baseUrl: String get() = "http://127.0.0.1:${server.address.port}"

        init {
            server.createContext("/") { exchange ->
                val path = exchange.requestURI.path
                requests.add(Request(path, exchange.requestHeaders.getFirst("Authorization"),
                    exchange.requestHeaders.getFirst("X-Autoapi-Contract"), exchange.requestBody.readAllBytes().toString(UTF_8)))
                val response = when (path) {
                    "/v1/models" -> """{"object":"list","data":[{"id":"contract-chat"},{"id":"contract-embedding"}]}"""
                    "/v1/chat/completions" -> """{"id":"chatcmpl-contract","object":"chat.completion","created":1,"model":"contract-chat","choices":[{"index":0,"message":{"role":"assistant","content":"loopback-ok"},"finish_reason":"stop"}],"usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2}}"""
                    "/v1/embeddings" -> """{"object":"list","model":"contract-embedding","data":[{"object":"embedding","index":0,"embedding":[0.25,0.75]}],"usage":{"prompt_tokens":1,"total_tokens":1}}"""
                    else -> """{"error":{"message":"Unexpected request path","type":"invalid_request_error"}}"""
                }.toByteArray(UTF_8)
                exchange.responseHeaders.add("Content-Type", "application/json")
                exchange.sendResponseHeaders(if (path in setOf("/v1/models", "/v1/chat/completions", "/v1/embeddings")) 200 else 400, response.size.toLong())
                exchange.responseBody.use { it.write(response) }
                exchange.close()
            }
            server.start()
        }

        override fun close() = server.stop(0)
    }

    @Test
    fun `actual factory preserves chat endpoint credentials custom headers and response`() {
        Loopback().use { endpoint ->
            val factory = OpenAiCompatibleModelFactory(endpoint.baseUrl, "acceptance-test-not-a-secret", null, null,
                mapOf("X-Autoapi-Contract" to "preserved"))
            val llm = factory.openAiCompatibleLlm("contract-chat", PricingModel.ALL_YOU_CAN_EAT, "contract-provider", null) as SpringAiLlmService
            assertEquals("loopback-ok", llm.chatModel.call("contract prompt"))
            assertEquals("contract-provider", llm.provider)
            val request = endpoint.requests.single()
            assertEquals("/v1/chat/completions", request.path)
            assertEquals("Bearer acceptance-test-not-a-secret", request.authorization)
            assertEquals("preserved", request.header)
            assertTrue(request.body.contains("contract-chat"))
            assertTrue(request.body.contains("contract prompt"))
        }
    }

    @Test
    fun `actual factory preserves embedding endpoint model dimensions and values`() {
        Loopback().use { endpoint ->
            val factory = OpenAiCompatibleModelFactory(endpoint.baseUrl, "acceptance-test-not-a-secret", null, null)
            val embedding = factory.openAiCompatibleEmbeddingService("contract-embedding", "contract-provider", 2)
            assertEquals(2, embedding.dimensions)
            assertArrayEquals(floatArrayOf(0.25f, 0.75f), embedding.embed("contract embedding"))
            val request = endpoint.requests.single()
            assertEquals("/v1/embeddings", request.path)
            assertEquals("Bearer acceptance-test-not-a-secret", request.authorization)
            assertTrue(request.body.contains("contract-embedding"))
        }
    }

    @Test
    fun `actual Docker configuration discovers registers and calls chat and embedding models`() {
        Loopback().use { endpoint ->
            val beans = DefaultListableBeanFactory()
            val properties = ConfigurableModelProviderProperties(defaultEmbeddingModel = "contract-embedding")
            val config = DockerLocalModelsConfig(DockerRetryProperties().apply { maxAttempts = 1 },
                DockerConnectionProperties().apply { baseUrl = endpoint.baseUrl }, beans, properties, ObjectProviders.empty())
            val initialized = config.dockerLocalModelsInitializer()
            assertEquals(setOf("contract-chat", "contract-embedding"), initialized.registeredLlms.map { it.modelId }.toSet())
            val chat = beans.getSingleton("dockerModel-contract-chat") as SpringAiLlmService
            val embedding = beans.getSingleton("dockerModel-contract-embedding") as SpringAiEmbeddingService
            assertEquals("loopback-ok", chat.chatModel.call("docker prompt"))
            assertArrayEquals(floatArrayOf(0.25f, 0.75f), embedding.embed("docker embedding"))
            assertEquals(listOf("/v1/models", "/v1/chat/completions", "/v1/embeddings"), endpoint.requests.map { it.path })
            assertTrue(endpoint.requests[1].body.contains("contract-chat"))
            assertTrue(endpoint.requests[2].body.contains("contract-embedding"))
        }
    }
}
