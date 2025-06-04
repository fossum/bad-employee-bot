
import asyncio
import os
import pytest
import sys

from gemini_client import GeminiClient


@pytest.fixture(scope="module")
def event_loop():
    """Overrides pytest-asyncio default event_loop fixture to be module-scoped."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
async def gemini_client_ft():
    """Fixture to provide an initialized GeminiClient for functional tests.

    Skips tests if the API key is not found.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY environment variable not set. Skipping functional tests.")

    client = GeminiClient(api_key=api_key)
    return client

@pytest.mark.asyncio
async def test_generate_single_response(gemini_client_ft: GeminiClient):
    """Tests the generate_response method for a single, non-chat interaction."""
    prompt = "What is the main component of Earth's atmosphere?"
    print(f"\n[FT] Sending prompt to generate_response: '{prompt}'")
    response = await gemini_client_ft.generate_response(prompt)
    print(f"[FT] Received response: '{response}'")

    assert response is not None, "Response should not be None"
    assert isinstance(response, str), "Response should be a string"
    assert len(response) > 0, "Response should not be empty"
    assert "Sorry, I encountered an error" not in response, "Response should not be a client-side error message"
    assert "Sorry, I couldn't get a valid response" not in response, "Response should not indicate an invalid response structure"
    # A very basic check for content (optional and can be flaky with LLMs)
    # assert "nitrogen" in response.lower() # Example, adjust based on expected output

@pytest.mark.asyncio
async def test_chat_interaction(gemini_client_ft: GeminiClient):
    """Tests the chat functionality: starting a chat and sending messages."""
    await gemini_client_ft.start_chat() # start_chat is async
    assert gemini_client_ft.chat is not None, "Chat session should be initialized after start_chat()"

    messages = [
        "Hello! Can you tell me a short story?",
        "What was the main character's name in that story?"
    ]

    for i, msg in enumerate(messages):
        print(f"\n[FT] Sending chat message ({i+1}): '{msg}'")
        response = await gemini_client_ft.send_chat_message(msg)
        print(f"[FT] Received chat response ({i+1}): '{response}'")

        assert response is not None, f"Chat response {i+1} should not be None"
        assert isinstance(response, str), f"Chat response {i+1} should be a string"
        assert len(response) > 0, f"Chat response {i+1} should not be empty"
        assert "Sorry, I encountered an error" not in response, f"Chat response {i+1} should not be a client-side error message"
        assert "Sorry, I couldn't get a valid chat response" not in response, f"Chat response {i+1} should not indicate an invalid response structure"
