
import os
import asyncio
import logging
from typing import Sequence

import discord

import google.generativeai as genai


class GeminiClient:
    """A client to interact with the Google Gemini API."""

    PROMPT_BASIS = """
    Your are often called bad employee, bad employee bot or
    something similar.

    You are a bad employee at a software company. You are
    skilled at what you do, but annoying to talk to. You
    know how to write good Perl code, but would rather
    everyone used Python instead.
    """

    PROMPT_REQUEST = """
    Write a snarky response to this user.
    """

    def __init__(self, api_key):
        """Initializes the Gemini client with the provided API key.

        Args:
            api_key (str): Your Google AI Studio API key.
        """
        if not api_key:
            raise ValueError("API key for Gemini not provided or found.")
        genai.configure(api_key=api_key)
        # Initialize the GenerativeModel. You can choose a specific model.
        # For text generation, 'gemini-2.5-flash' is a good versatile choice.
        # Can be overridden via GEMINI_MODEL environment variable.
        model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        self.model = genai.GenerativeModel(model_name)
        self.chat = None # For conversational history
        self._logger = logging.getLogger(__name__)

    async def generate_response(self, message: discord.Message, previous_msgs: Sequence[discord.Message] = None) -> str:
        """Generates a response from the Gemini model based on the prompt.

        Args:
            prompt_text (str): The text prompt to send to Gemini.
            previous_msgs (Sequence[str], optional): Previous messages from the same user.
        Returns:
            str: The generated text response from Gemini, or an error message.
        """
        prompt = GeminiClient.PROMPT_BASIS

        # Resolve current message content whether we received a discord.Message
        # or a plain string.
        current_content = getattr(message, 'clean_content', None) or str(message)

        if previous_msgs:
            # Prefer a stable mention token (`<@id>`) and also include a
            # human-readable display name (global_name or username) so the
            # prompt contains both the canonical Discord mention and a readable
            # label for the model.
            if hasattr(message, 'author') and getattr(message.author, 'id', None):
                author_display = getattr(message.author, 'global_name', getattr(message.author, 'name', 'unknown'))
                author_mention = f"<@{message.author.id}>"
            else:
                author_display = 'unknown'
                author_mention = 'unknown'

            prompt += f"""

            This user is named {author_display} (Discord mention: {author_mention})

            Previous messages from this user, starting with the UTC epoch they sent it, the channel sent and the message:
            *
            """
            # Use a different variable name in comprehension to avoid shadowing.
            prompt += "\n * ".join([f"{m.created_at.timestamp()},{m.channel.name},{m.clean_content}" for m in previous_msgs])

        prompt += f"""

        User's current message:
        {current_content}
        """

        # Debug: log a truncated preview of the prompt to help troubleshooting.
        self._logger.debug(f"Gemini prompt preview: {prompt[:400].replace('\n','\\n')}... (len={len(prompt)})")

        try:
            # For a simple, non-chat generation. Protect with a timeout so the
            # bot doesn't hang indefinitely if the API is slow or unreachable.
            try:
                response = await asyncio.wait_for(self.model.generate_content_async(prompt), timeout=15)
            except asyncio.TimeoutError:
                self._logger.error("Timed out waiting for Gemini response.")
                return "Sorry, the AI service is taking too long to respond. Try again later."

            # Inspect common response shapes and return sensible text.
            # Prefer `parts`, then `candidates`, then `text`.
            if hasattr(response, 'parts') and response.parts:
                return getattr(response.parts[0], 'text', str(response.parts[0]))
            if hasattr(response, 'candidates') and response.candidates:
                # Some SDK versions use `candidates` with `.content`.
                candidate = response.candidates[0]
                return getattr(candidate, 'content', str(candidate))
            if hasattr(response, 'text') and response.text:
                return response.text

            # Fallback: stringify response for debugging.
            self._logger.warning(f"Unexpected Gemini response shape: {response}")
            return "Sorry, I couldn't get a valid response from Gemini."
        except Exception as e:
            print(f"Error generating response from Gemini: {e}")
            return f"Sorry, I encountered an error while trying to talk to Gemini: {e}"

    async def start_chat(self, history=None):
        """Starts a new chat session or continues from existing history.

        Args:
            history (list, optional): A list of previous chat messages
                                      following the Gemini API's format.
                                      e.g., [{'role':'user', 'parts': ['Hello!']},
                                             {'role':'model', 'parts': ['Hi there!']}]
        """
        self.chat = self.model.start_chat(history=history or [])
        print("Gemini chat session started.")

    async def send_chat_message(self, message: str) -> str:
        """Sends a message in an ongoing chat session and gets a response.

        Args:
            message (str): The user's message to send to the chat.
        Returns:
            str: The model's response, or an error message.
        """
        if not self.chat:
            # return "Chat session not started. Please use 'start_chat' first or use 'generate_response' for single turns."
            # Alternatively, auto-start a chat if one isn't active
            await self.start_chat()

        try:
            response = await self.chat.send_message_async(message)
            if response.parts:
                return response.parts[0].text
            elif response.text:
                return response.text
            else:
                return "Sorry, I couldn't get a valid chat response from Gemini."
        except Exception as e:
            print(f"Error sending chat message to Gemini: {e}")
            return f"Sorry, I encountered an error during our chat: {e}"

# Example of how to use (optional, for testing this file directly):
if __name__ == '__main__':
    import asyncio
    # You'd typically load this from an environment variable or a config file
    YOUR_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not YOUR_GEMINI_API_KEY:
        print("Please set the GEMINI_API_KEY environment variable.")
    else:
        gemini_bot = GeminiClient(api_key=YOUR_GEMINI_API_KEY)

        async def main():
            # Test single response
            # prompt = "What is the speed of light?"
            # print(f"User: {prompt}")
            # response = await gemini_bot.generate_response(prompt)
            # print(f"Gemini: {response}")

            # Test chat
            await gemini_bot.start_chat()
            print("Gemini Chat Started. Type 'quit' to end.")
            while True:
                user_input = input("You: ")
                if user_input.lower().strip() == 'quit':
                    break
                gemini_response = await gemini_bot.send_chat_message(user_input)
                print(f"Gemini: {gemini_response}")

        asyncio.run(main())
