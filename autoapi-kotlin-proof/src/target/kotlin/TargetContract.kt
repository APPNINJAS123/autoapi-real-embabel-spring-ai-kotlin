package com.embabel.autoapi

import com.openai.client.OpenAIClient
import com.openai.client.okhttp.OpenAIOkHttpClient
import io.micrometer.observation.ObservationRegistry
import org.springframework.ai.document.MetadataMode
import org.springframework.ai.openai.OpenAiChatModel
import org.springframework.ai.openai.OpenAiChatOptions
import org.springframework.ai.openai.OpenAiEmbeddingModel
import org.springframework.ai.openai.OpenAiEmbeddingOptions
import java.time.Duration

fun targetOpenAiClient(): OpenAIClient =
    OpenAIOkHttpClient.builder()
        .apiKey("acceptance-test-not-a-secret")
        .baseUrl("http://127.0.0.1:9/v1")
        .timeout(Duration.ofMillis(1_000))
        .putHeader("X-AutoAPI-Contract", "true")
        .build()

fun targetChatModel(client: OpenAIClient): OpenAiChatModel =
    OpenAiChatModel.builder()
        .openAiClient(client)
        .options(
            OpenAiChatOptions.builder()
                .model("contract-model")
                .customHeaders(mapOf("X-Chat-Contract" to "true"))
                .build()
        )
        .observationRegistry(ObservationRegistry.NOOP)
        .build()

fun targetEmbeddingModel(client: OpenAIClient): OpenAiEmbeddingModel =
    OpenAiEmbeddingModel(
        client,
        MetadataMode.EMBED,
        OpenAiEmbeddingOptions.builder().model("contract-embedding").build(),
        ObservationRegistry.NOOP,
    )
