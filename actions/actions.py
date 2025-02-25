from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from chapter_data import chapter_data
import random

class ActionExplainChapter(Action):
    def name(self) -> Text:
        return "action_explain_chapter"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        chapter = tracker.get_slot("chapter")  # Retrieve chapter slot

        if chapter in chapter_data:
            content = chapter_data[chapter]
            topics_list = list(content["topics"].keys())  # Get topics
            topics_text = "\n".join([f"- {topic}" for topic in topics_list])

            response_text = (
                f"📘 **Chapter {chapter}: {content['title']}**\n\n"
                f"{content['overview']}\n\n"
                f"📌 **Topics in this chapter:**\n{topics_text}\n\n"
                "Would you like to learn about a specific topic, take a quiz, or explore another chapter?"
            )

            dispatcher.utter_message(text=response_text)
            return [SlotSet("chapter", chapter)]
        else:
            dispatcher.utter_message(text="❌ Sorry, I couldn't find details on that chapter.")
        
        return []
    
class ActionListChapters(Action):
    def name(self) -> Text:
        return "action_list_chapters"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        chapters = chapter_data.keys()
        chapter_list = "\n".join([f"- Chapter {num}: {chapter_data[num]['title']}" for num in chapters])
        dispatcher.utter_message(text=f"📖 **Available Chapters:**\n{chapter_list}\n\nType 'Chapter [number]' to explore a specific chapter.")
        return []

import logging

logger = logging.getLogger(__name__)

class ActionExplainTopic(Action):
    def name(self) -> Text:
        return "action_explain_topic"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        chapter = tracker.get_slot("chapter")
        requested_topic = tracker.get_slot("topic")  # Get user's requested topic
        topic_index = tracker.get_slot("topic_index") or 0

        logger.debug(f"DEBUG: Requested topic: {requested_topic}")
        logger.debug(f"DEBUG: Current topic index: {topic_index}")

        if not chapter:
            dispatcher.utter_message(text="❌ No chapter is selected. Please start with a chapter request.")
            return []

        if chapter in chapter_data:
            topics = list(chapter_data[chapter]["topics"].keys())  # Extract topic names

            # Normalize topic names to lowercase for case-insensitive matching
            topics_lower = {t.lower(): t for t in topics}
            requested_topic_lower = requested_topic.lower() if requested_topic else None

            logger.debug(f"DEBUG: Available topics: {topics}")

            # 🔹 Prioritize Direct Topic Matching
            if requested_topic_lower in topics_lower:
                topic_title = topics_lower[requested_topic_lower]
                topic_description = chapter_data[chapter]["topics"][topic_title]

                logger.debug(f"DEBUG: Matched topic: {topic_title}")

                dispatcher.utter_message(text=f"📖 **{topic_title}**\n{topic_description}")
                return [SlotSet("topic", topic_title)]  # ✅ Ensure slot updates properly

            # 🔹 If no specific topic requested, continue sequentially
            if topic_index < len(topics):
                topic_title = topics[topic_index]
                topic_description = chapter_data[chapter]["topics"][topic_title]

                logger.debug(f"DEBUG: Sequential topic: {topic_title}")

                dispatcher.utter_message(text=f"📖 **{topic_title}**\n{topic_description}")
                return [SlotSet("topic_index", topic_index + 1)]  # Move to next topic

            else:
                dispatcher.utter_message(text="✅ You've reached the last topic in this chapter. Would you like to take a quiz or explore a new chapter?")
                return [SlotSet("topic_index", 0)]  # Reset after last topic
        else:
            dispatcher.utter_message(text="❌ No topics found for this chapter.")
        
        return []



class ActionManageQuiz(Action):
    def name(self) -> Text:
        return "action_manage_quiz"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        chapter = tracker.get_slot("chapter")
        quiz_index = tracker.get_slot("quiz_index") or 0
        quiz_questions = tracker.get_slot("quiz_questions")

        # If user is starting the quiz, fetch questions
        if not quiz_questions:
            if chapter in chapter_data and "quiz" in chapter_data[chapter]:
                quiz_questions = chapter_data[chapter]["quiz"]
                dispatcher.utter_message(text="📝 **Quiz Time!** Let's begin!")
                quiz_index = 0
            else:
                dispatcher.utter_message(text="❌ Sorry, no quiz questions are available for this chapter.")
                return []

        # If quiz is already running, validate the last answer
        else:
            user_response = tracker.latest_message.get("text", "").strip().lower()
            correct_answer = quiz_questions[quiz_index]["answer"].lower()
            options = quiz_questions[quiz_index]["options"]

            # Convert user input (a, b, c, d) to the corresponding answer text
            option_letters = ["a", "b", "c", "d"]
            selected_option = None

            if user_response in option_letters:
                selected_index = option_letters.index(user_response)
                if selected_index < len(options):  # Ensure the index is within the options range
                    selected_option = options[selected_index].lower()
            
            # Debugging
            print(f"DEBUG: User Response: {user_response}")
            print(f"DEBUG: Selected Option: {selected_option}")
            print(f"DEBUG: Correct Answer: {correct_answer}")

            # Validate answer by checking full text or corresponding letter-mapped text
            if selected_option == correct_answer or user_response == correct_answer:
                dispatcher.utter_message(text="✅ Correct!")
            else:
                dispatcher.utter_message(text=f"❌ Incorrect. The correct answer is: **{correct_answer}**")

            # Move to next question
            quiz_index += 1

        # Check if quiz is completed
        if quiz_index < len(quiz_questions):
            question = quiz_questions[quiz_index]
            options_text = "\n".join([f"{chr(97 + i)}) {opt}" for i, opt in enumerate(question['options'])])
            dispatcher.utter_message(text=f"❓ {question['question']}\n{options_text}\n\n(Reply with a, b, c, or d)")
            return [SlotSet("quiz_questions", quiz_questions), SlotSet("quiz_index", quiz_index)]
        else:
            dispatcher.utter_message(text="🎉 Quiz completed! Would you like to review a topic or start another quiz?")
            return [SlotSet("quiz_index", 0), SlotSet("quiz_questions", None)]
