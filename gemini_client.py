
import os
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
        # For text generation, 'gemini-1.5-flash' is a good versatile choice.
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.chat = None # For conversational history

    async def generate_response(self, message: discord.Message, previous_msgs: Sequence[discord.Message] = None) -> str:
        """Generates a response from the Gemini model based on the prompt.

        Args:
            prompt_text (str): The text prompt to send to Gemini.
            previous_msgs (Sequence[str], optional): Previous messages from the same user.
        Returns:
            str: The generated text response from Gemini, or an error message.
        """
        prompt = GeminiClient.PROMPT_BASIS
        if previous_msgs:
            prompt += f"""

            This user is named @{message.author.global_name}

            Previous messages from this user, starting with the UTC epoch they sent it, the channel sent and the message:
            *
            """
            prompt += "\n * ".join([f"{message.created_at.timestamp()},{message.channel.name},{message.clean_content}" for message in previous_msgs])
        prompt += f"""

        User's current message:
        {message}
        """

        try:
            # For a simple, non-chat generation:
            response = await self.model.generate_content_async(prompt)
            # Ensure you access the text part correctly.
            # The structure might vary slightly based on the response type.
            # It's good to inspect response.parts if response.text is not available.
            if response.parts:
                 return response.parts[0].text
            elif response.text: # Fallback if .text attribute exists directly
                 return response.text
            else:
                 return "Sorry, I couldn't get a valid response from Gemini. The response structure might have changed."
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
