package com.embabel.autoapi

import org.springframework.ai.model.SimpleApiKey
import org.springframework.ai.openai.api.OpenAiApi

fun baselineOpenAiApi(): OpenAiApi =
    OpenAiApi.builder()
        .apiKey(SimpleApiKey("acceptance-test-not-a-secret"))
        .build()
