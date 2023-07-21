# Importing necessary modules
import streamlit as st
import sqlite3
from time import sleep
import random
from hugchat_api import HuggingChat
from hugchat.hugchat import ChatBot
import speech_recognition as sr

# Create a connection to the database
db_path = "C:/Users/suhas/PycharmProjects/Chat/users.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Create users table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS users
             (username TEXT, password TEXT)''')
conn.commit()


def create_user_table():
    # Create users table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT, password TEXT)''')
    conn.commit()


def add_user(username, password):
    # Insert a new user into the table
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
              (username, password))
    conn.commit()


def authenticate_user(username, password):
    # Check if the user exists in the table
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username, password))
    return c.fetchone()


def login():
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login 🔓"):
        user = authenticate_user(username, password)
        if user:
            st.success("Logged in as {}".format(user[0]))
            with st.spinner("Loading Chatbot"):
                sleep(random.randint(2, 6))
            st.session_state["logged_in"] = True
            return True
        else:
            st.error("Invalid username or password")
    return False


def signup():
    st.subheader("Create New Account")
    new_username = st.text_input("Username")
    new_password = st.text_input("Password", type="password")

    if st.button("Sign Up 📝"):
        if new_username and new_password:
            add_user(new_username, new_password)
            sleep(random.randint(2, 6))
            st.success("Account created successfully")
            st.info("Please log in.")

        else:
            st.warning("Username and password are required")


def main():
    create_user_table()

    st.title("IntelliChat🤖")
    st.title("Access and Registration")
    st.sidebar.title("Navigation 🧭")

    pages = {
        "Login": login,
        "Signup": signup
    }

    page = st.sidebar.radio("Pages", tuple(pages.keys()))

    if page in pages:
        pages[page]()

    # Redirection code after authentication
    if st.session_state.get("logged_in"):
        chatbot()

        # Add speech recognition button
        if st.button("Speech Recognition 🎤"):
            speech_recognition()


# Home page code for displaying the messages
def chatbot():
    st.title("AI powered Large-Language Model Chatbot 🤖💬")
    st.markdown('''
         - This may produce inaccurate information about people, places, or facts
         - Limited knowledge of world and events after 2021


         💡 Note: No Sign-in or API key required!
    ''')
    st.markdown("Press 👇 button to activate Speech Recognition.")

    # Giving access to HugChat API
    EMAIL = st.secrets["db_email"]
    PASSWD = st.secrets["db_password"]
    COOKIE_STORE_PATH = "./usercookies"

    HUG = HuggingChat(max_thread=1)

    sign = HUG.getSign(EMAIL, PASSWD)
    try:
        cookies = sign.login(save=True, cookie_dir_path=COOKIE_STORE_PATH)
    except Exception as e:
        st.error(f"An error occurred during login: {str(e)}")
        st.stop()
    cookies = sign.loadCookiesFromDir(cookie_dir_path=COOKIE_STORE_PATH)

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app return
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Function for generating the response
    def generate_response(dialogue_history):
        chatbot = ChatBot(cookies=cookies.get_dict())
        response = chatbot.chat(dialogue_history, stream=True)
        if isinstance(response, str):
            return response
        else:
            return response.delta.get("content", "")

    # Accept user input:
    if prompt := st.chat_input("Enter a message"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Append the dialogue history to the user's prompt
        dialogue_history = "\n".join([message["content"] for message in st.session_state.messages])
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        # Display assistant response in chat message container
        with st.spinner('Generating response....'):
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""

                try:
                    for response in generate_response(dialogue_history):
                        full_response += response
                        message_placeholder.markdown(full_response + "▌")
                        sleep(0.01)
                    message_placeholder.markdown(full_response)

                    # Check if there are follow-up questions
                    if "?" in prompt:
                        # Update the chat history with the assistant's response
                        st.session_state.messages.append({"role": "assistant", "content": full_response})
                        # Clear the chat input box
                        st.session_state.prompt = ""
                        # Set the chat input box value to the assistant's response
                        st.chat_input("Follow-up question", value=full_response)

                    # Update the chat history
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                except Exception as e:
                    st.error(f"An error occurred during response generation: {str(e)}")
                    # Update the chat history with the error message
                    st.session_state.messages.append({"role": "assistant", "content": f"An error occurred: {str(e)}"})


# Speech recognition function
def speech_recognition():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        st.info("Listening...")

        audio = recognizer.listen(source)

    try:
        prompt = recognizer.recognize_google(audio)
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_input("Enter a message", value=prompt)

    except sr.UnknownValueError:
        st.warning("Sorry, I could not understand your speech.")
    except sr.RequestError:
        st.error("Sorry, speech recognition service is currently unavailable.")


# Script initialization
if __name__ == "__main__":
    main()
