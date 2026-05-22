"""Draftspace Deploy — MongoDB helper"""
import os
from pymongo import MongoClient
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://santoshks_db_user:viefoCaPp3CMCqTq@cluster0.v8wfkok.mongodb.net/Draftspace?retryWrites=true&w=majority&appName=Cluster0")
try:
    _client=MongoClient(MONGO_URI,serverSelectionTimeoutMS=5000)
    _db=_client.get_database("Draftspace"); _ok=True
except Exception as e:
    print(f"offline: {e}"); _db=None; _ok=False
_FORMS=[
  {
    "_id": "69cbaf8e5e1c76b9d6db9d71",
    "user_id": "69cbaf893e4b965c3ac9bf4f",
    "title": "jain",
    "description": "",
    "slug": "DZwLjqApU3A",
    "pages": [
      {
        "fields": [
          {
            "help": "",
            "id": "f_1774956433150",
            "label": "Short Answer",
            "placeholder": "Type here...",
            "required": false,
            "type": "short_text"
          },
          {
            "help": "",
            "id": "f_1774956434038",
            "label": "Long Answer",
            "placeholder": "Type here...",
            "required": false,
            "type": "long_text"
          },
          {
            "help": "",
            "id": "f_1774956435175",
            "label": "Phone Number",
            "placeholder": "+91 XXXXX XXXXX",
            "required": false,
            "type": "phone"
          },
          {
            "help": "",
            "id": "f_1774956435438",
            "label": "Short Answer",
            "placeholder": "Type here...",
            "required": false,
            "type": "short_text"
          },
          {
            "help": "",
            "id": "f_1774956435758",
            "label": "Number",
            "placeholder": "0",
            "required": false,
            "type": "number"
          },
          {
            "help": "",
            "id": "f_1774956436200",
            "label": "Email Address",
            "placeholder": "email@example.com",
            "required": true,
            "type": "email"
          },
          {
            "help": "",
            "id": "f_1774956436471",
            "label": "Multiple Choice",
            "options": [
              "Option 1",
              "Option 2",
              "Option 3"
            ],
            "placeholder": "",
            "required": false,
            "type": "radio"
          },
          {
            "help": "",
            "id": "f_1774956436774",
            "label": "Checkboxes",
            "options": [
              "Option 1",
              "Option 2",
              "Option 3"
            ],
            "placeholder": "",
            "required": false,
            "type": "checkbox"
          },
          {
            "help": "",
            "id": "f_1774956437303",
            "label": "Rating",
            "max_rating": 5,
            "placeholder": "",
            "required": false,
            "type": "rating"
          },
          {
            "help": "",
            "id": "f_1774956437558",
            "label": "Linear Scale",
            "placeholder": "",
            "required": false,
            "scale_max": 10,
            "type": "scale"
          }
        ],
        "id": "page_1",
        "title": "Page 1"
      },
      {
        "id": "p_1774956568606",
        "title": "Page 2",
        "fields": [
          {
            "id": "f_1774956572838",
            "type": "scale",
            "label": "Linear Scale",
            "help": "",
            "required": false,
            "placeholder": "",
            "scale_max": 10
          },
          {
            "id": "f_1774956574742",
            "type": "rating",
            "label": "Rating",
            "help": "",
            "required": false,
            "placeholder": "",
            "max_rating": 5
          }
        ]
      }
    ],
    "settings": {
      "confirmation_message": "Thank you for your response!",
      "is_published": true,
      "notify_email": "",
      "notify_on_submit": false,
      "redirect_url": "",
      "show_progress": true
    },
    "theme": {
      "accent_color": "#2980B9",
      "bg_color": "#E8F4FD",
      "button_text": "Submit",
      "card_color": "#FFFFFF",
      "cover_image": "linear-gradient(135deg,#003366,#0066CC)",
      "font": "Inter",
      "header_color": "#0F2027",
      "header_style": "gradient",
      "text_color": "#1A2A3A"
    },
    "created_at": "2026-03-31T11:27:10.156000",
    "updated_at": "2026-03-31T11:29:35.322000",
    "response_count": 0,
    "responses": []
  },
  {
    "_id": "69ce0c8e2cf0997c972c7ef5",
    "user_id": "69cbaf893e4b965c3ac9bf4f",
    "title": "Mental Health Awareness Research Survey",
    "description": "Help us understand mental health awareness and perceptions in the community. Your responses will contribute to valuable research.",
    "slug": "bG7vDumTMf0",
    "pages": [
      {
        "fields": [
          {
            "help": "Please enter your age in years.",
            "id": "f_1",
            "label": "What is your age?",
            "placeholder": "e.g., 25",
            "required": true,
            "type": "short_text"
          },
          {
            "help": "",
            "id": "f_2",
            "label": "What is your gender?",
            "options": [
              "Male",
              "Female",
              "Non-binary",
              "Prefer not to say",
              "Other"
            ],
            "required": true,
            "type": "dropdown"
          },
          {
            "help": "",
            "id": "f_3",
            "label": "What is your highest level of education completed?",
            "options": [
              "High school or less",
              "Some college",
              "Associate degree",
              "Bachelor's degree",
              "Master's degree",
              "Doctorate or professional degree",
              "Prefer not to say"
            ],
            "required": true,
            "type": "dropdown"
          },
          {
            "help": "",
            "id": "f_4",
            "label": "What is your current employment status?",
            "options": [
              "Employed full-time",
              "Employed part-time",
              "Self-employed",
              "Unemployed",
              "Student",
              "Retired",
              "Prefer not to say"
            ],
            "required": true,
            "type": "dropdown"
          }
        ],
        "id": "page_1",
        "title": "Demographics"
      },
      {
        "fields": [
          {
            "help": "",
            "id": "f_5",
            "label": "How familiar are you with common mental health conditions (e.g., anxiety, depression)?",
            "options": [
              "Very familiar",
              "Somewhat familiar",
              "Neutral",
              "Not very familiar",
              "Not familiar at all"
            ],
            "required": true,
            "type": "radio"
          },
          {
            "help": "",
            "id": "f_6",
            "label": "Which of the following mental health conditions have you heard of? (Select all that apply)",
            "options": [
              "Anxiety disorders",
              "Depression",
              "Bipolar disorder",
              "Schizophrenia",
              "Post-traumatic stress disorder (PTSD)",
              "Obsessive-compulsive disorder (OCD)",
              "Eating disorders",
              "None of the above"
            ],
            "required": true,
            "type": "checkbox"
          },
          {
            "help": "",
            "id": "f_7",
            "label": "Do you believe mental health is as important as physical health?",
            "options": [
              "Strongly agree",
              "Agree",
              "Neutral",
              "Disagree",
              "Strongly disagree"
            ],
            "required": true,
            "type": "radio"
          },
          {
            "help": "",
            "id": "f_8",
            "label": "In your opinion, what are the biggest challenges people face when seeking help for mental health issues?",
            "placeholder": "Please share your thoughts...",
            "required": false,
            "type": "long_text"
          }
        ],
        "id": "page_2",
        "title": "Mental Health Awareness"
      },
      {
        "fields": [
          {
            "help": "",
            "id": "f_9",
            "label": "Have you or someone close to you ever experienced a mental health condition?",
            "options": [
              "Yes, myself",
              "Yes, someone close to me",
              "No",
              "Prefer not to say"
            ],
            "required": true,
            "type": "radio"
          },
          {
            "help": "",
            "id": "f_10",
            "label": "How comfortable would you feel discussing mental health issues with friends or family?",
            "options": [
              "Very comfortable",
              "Somewhat comfortable",
              "Neutral",
              "Somewhat uncomfortable",
              "Very uncomfortable"
            ],
            "required": true,
            "type": "radio"
          },
          {
            "help": "1 = Very low, 5 = Very high",
            "id": "f_11",
            "label": "On a scale of 1 to 5, how would you rate the level of mental health awareness in your community?",
            "max_rating": 5,
            "required": true,
            "type": "rating"
          },
          {
            "help": "",
            "id": "f_12",
            "label": "What do you think could be done to improve mental health awareness and support in your community?",
            "placeholder": "Please share your suggestions...",
            "required": false,
            "type": "long_text"
          }
        ],
        "id": "page_3",
        "title": "Personal Experience and Perceptions"
      }
    ],
    "settings": {
      "confirmation_message": "Thank you for participating in our research survey! Your input is greatly appreciated.",
      "is_published": true,
      "notify_email": "",
      "notify_on_submit": false,
      "redirect_url": "",
      "show_progress": true
    },
    "theme": {
      "accent_color": "#2D6A4F",
      "bg_color": "#F8F9FA",
      "button_text": "Submit",
      "card_color": "#FFFFFF",
      "cover_image": "",
      "font": "DM Sans",
      "header_color": "#134E5E",
      "text_color": "#212529"
    },
    "created_at": "2026-04-02T06:28:30.351000",
    "updated_at": "2026-04-02T07:32:18.228000",
    "response_count": 0,
    "responses": []
  },
  {
    "_id": "69ce0ca52cf0997c972c7ef6",
    "user_id": "69cbaf893e4b965c3ac9bf4f",
    "title": "jain",
    "description": "",
    "slug": "p6_nicqyY3g",
    "pages": [
      {
        "fields": [],
        "id": "page_1",
        "title": "Page 1"
      },
      {
        "id": "p_1775111336055",
        "title": "Page 2",
        "fields": []
      }
    ],
    "settings": {
      "confirmation_message": "Thank you for your response!",
      "is_published": false,
      "notify_email": "",
      "notify_on_submit": false,
      "redirect_url": "",
      "show_progress": true
    },
    "theme": {
      "accent_color": "#FF8C00",
      "bg_color": "#F8F9FA",
      "button_text": "Submit",
      "card_color": "#FFFFFF",
      "cover_image": "",
      "font": "DM Sans",
      "header_color": "#1A1A2E",
      "header_style": "gradient",
      "text_color": "#212529"
    },
    "created_at": "2026-04-02T06:28:53.396000",
    "updated_at": "2026-04-02T06:29:17.635000",
    "response_count": 0,
    "responses": []
  },
  {
    "_id": "69ce0e0025b4e4e635a9ce6c",
    "user_id": "69cbaf893e4b965c3ac9bf4f",
    "title": "Mental Health Awareness Research Survey",
    "description": "Help us understand mental health awareness and perceptions in our community. Your responses will remain confidential.",
    "slug": "oKpsSjlx41M",
    "pages": [
      {
        "fields": [
          {
            "help": "Please enter your age in years",
            "id": "f_1",
            "label": "What is your age?",
            "placeholder": "e.g., 25",
            "required": true,
            "type": "short_text"
          },
          {
            "help": "",
            "id": "f_2",
            "label": "What is your gender?",
            "options": [
              "Male",
              "Female",
              "Non-binary",
              "Prefer not to say",
              "Other"
            ],
            "required": true,
            "type": "dropdown"
          },
          {
            "help": "",
            "id": "f_3",
            "label": "What is your highest level of education completed?",
            "options": [
              "High school or less",
              "Some college",
              "Associate degree",
              "Bachelor's degree",
              "Master's degree",
              "Doctorate or professional degree",
              "Prefer not to say"
            ],
            "required": true,
            "type": "dropdown"
          },
          {
            "help": "",
            "id": "f_4",
            "label": "Which of the following best describes your current employment status?",
            "options": [
              "Employed full-time",
              "Employed part-time",
              "Self-employed",
              "Unemployed",
              "Student",
              "Retired",
              "Prefer not to say"
            ],
            "required": true,
            "type": "dropdown"
          }
        ],
        "id": "page_1",
        "title": "Demographics"
      },
      {
        "fields": [
          {
            "help": "",
            "id": "f_5",
            "label": "How familiar are you with common mental health disorders (e.g., depression, anxiety, PTSD)?",
            "options": [
              "Very familiar",
              "Somewhat familiar",
              "Neutral",
              "Not very familiar",
              "Not familiar at all"
            ],
            "required": true,
            "type": "radio"
          },
          {
            "help": "",
            "id": "f_6",
            "label": "Which of the following mental health resources have you heard of? (Select all that apply)",
            "options": [
              "Crisis hotlines (e.g., 988 Suicide & Crisis Lifeline)",
              "Therapy or counseling services",
              "Support groups (e.g., NAMI, AA)",
              "Mental health apps (e.g., Headspace, Calm)",
              "Workplace mental health programs",
              "School-based mental health services",
              "None of the above"
            ],
            "required": false,
            "type": "checkbox"
          },
          {
            "help": "",
            "id": "f_7",
            "label": "How comfortable would you feel discussing mental health issues with a friend or family member?",
            "options": [
              "Very comfortable",
              "Somewhat comfortable",
              "Neutral",
              "Somewhat uncomfortable",
              "Very uncomfortable"
            ],
            "required": true,
            "type": "radio"
          },
          {
            "help": "",
            "id": "f_8",
            "label": "Do you believe mental health is as important as physical health?",
            "options": [
              "Strongly agree",
              "Agree",
              "Neutral",
              "Disagree",
              "Strongly disagree"
            ],
            "required": true,
            "type": "radio"
          }
        ],
        "id": "page_2",
        "title": "Mental Health Awareness"
      },
      {
        "fields": [
          {
            "help": "We appreciate your time and feedback.",
            "id": "f_9",
            "label": "Thank you for your participation!",
            "type": "header"
          },
          {
            "help": "",
            "id": "f_10",
            "label": "Do you have any additional feedback or suggestions about mental health awareness in our community?",
            "placeholder": "Your feedback is valuable to us...",
            "required": false,
            "type": "long_text"
          },
          {
            "help": "Please rate your experience with this survey.",
            "id": "f_11",
            "label": "How would you rate this survey?",
            "max_rating": 5,
            "required": true,
            "type": "rating"
          }
        ],
        "id": "page_3",
        "title": "Feedback & Rating"
      }
    ],
    "settings": {
      "confirmation_message": "Thank you for participating in our Mental Health Awareness Research Survey! Your input is invaluable.",
      "is_published": false,
      "notify_email": "",
      "notify_on_submit": false,
      "redirect_url": "",
      "show_progress": true
    },
    "theme": {
      "accent_color": "#2D6A4F",
      "bg_color": "#F8F9FA",
      "button_text": "Submit",
      "card_color": "#FFFFFF",
      "cover_image": "",
      "font": "DM Sans",
      "header_color": "#134E5E",
      "text_color": "#212529"
    },
    "created_at": "2026-04-02T06:34:40.302000",
    "updated_at": "2026-04-02T06:35:43.970000",
    "response_count": 0,
    "responses": []
  },
  {
    "_id": "69ce30b635139c5892d9acd4",
    "user_id": "69cbaf893e4b965c3ac9bf4f",
    "title": "Student Exit Course Evaluation",
    "description": "Please provide feedback on the courses you have completed to help us improve our academic programs.",
    "slug": "d1fsPVGcN3o",
    "pages": [
      {
        "fields": [
          {
            "help": "",
            "id": "f_1",
            "label": "Full Name",
            "placeholder": "Enter your full name",
            "required": true,
            "type": "short_text"
          },
          {
            "help": "",
            "id": "f_2",
            "label": "Email Address",
            "placeholder": "Enter your email address",
            "required": true,
            "type": "email"
          },
          {
            "help": "",
            "id": "f_3",
            "label": "Student ID",
            "placeholder": "Enter your student ID",
            "required": true,
            "type": "short_text"
          },
          {
            "help": "",
            "id": "f_4",
            "label": "Program/Major",
            "placeholder": "Enter your program or major",
            "required": true,
            "type": "short_text"
          },
          {
            "id": "f_5",
            "label": "Course Evaluations",
            "type": "header"
          },
          {
            "help": "Enter the name of the first course you completed",
            "id": "f_6",
            "label": "Course Name 1",
            "placeholder": "e.g., Introduction to Computer Science",
            "required": true,
            "type": "short_text"
          },
          {
            "help": "Rate the overall quality of this course",
            "id": "f_7",
            "label": "Overall Quality of Course 1",
            "max_rating": 5,
            "required": true,
            "type": "rating"
          },
          {
            "help": "Rate the effectiveness of the instructor",
            "id": "f_8",
            "label": "Instructor Effectiveness in Course 1",
            "max_rating": 5,
            "required": true,
            "type": "rating"
          },
          {
            "help": "Rate the relevance of the course content",
            "id": "f_9",
            "label": "Course Content Relevance in Course 1",
            "max_rating": 5,
            "required": true,
            "type": "rating"
          },
          {
            "help": "Provide any additional comments or feedback for this course",
            "id": "f_10",
            "label": "Comments for Course 1",
            "placeholder": "Enter your comments here",
            "required": false,
            "type": "long_text"
          },
          {
            "help": "Enter the name of the second course you completed",
            "id": "f_11",
            "label": "Course Name 2",
            "placeholder": "e.g., Calculus I",
            "required": false,
            "type": "short_text"
          },
          {
            "help": "Rate the overall quality of this course",
            "id": "f_12",
            "label": "Overall Quality of Course 2",
            "max_rating": 5,
            "required": false,
            "type": "rating"
          },
          {
            "help": "Rate the effectiveness of the instructor",
            "id": "f_13",
            "label": "Instructor Effectiveness in Course 2",
            "max_rating": 5,
            "required": false,
            "type": "rating"
          },
          {
            "help": "Rate the relevance of the course content",
            "id": "f_14",
            "label": "Course Content Relevance in Course 2",
            "max_rating": 5,
            "required": false,
            "type": "rating"
          },
          {
            "help": "Provide any additional comments or feedback for this course",
            "id": "f_15",
            "label": "Comments for Course 2",
            "placeholder": "Enter your comments here",
            "required": false,
            "type": "long_text"
          },
          {
            "help": "Enter the name of the third course you completed",
            "id": "f_16",
            "label": "Course Name 3",
            "placeholder": "e.g., Physics 101",
            "required": false,
            "type": "short_text"
          },
          {
            "help": "Rate the overall quality of this course",
            "id": "f_17",
            "label": "Overall Quality of Course 3",
            "max_rating": 5,
            "required": false,
            "type": "rating"
          },
          {
            "help": "Rate the effectiveness of the instructor",
            "id": "f_18",
            "label": "Instructor Effectiveness in Course 3",
            "max_rating": 5,
            "required": false,
            "type": "rating"
          },
          {
            "help": "Rate the relevance of the course content",
            "id": "f_19",
            "label": "Course Content Relevance in Course 3",
            "max_rating": 5,
            "required": false,
            "type": "rating"
          },
          {
            "help": "Provide any additional comments or feedback for this course",
            "id": "f_20",
            "label": "Comments for Course 3",
            "placeholder": "Enter your comments here",
            "required": false,
            "type": "long_text"
          }
        ],
        "id": "page_1",
        "title": "Course Information"
      },
      {
        "fields": [
          {
            "help": "Rate your overall academic experience in the program",
            "id": "f_21",
            "label": "Overall Academic Experience",
            "max_rating": 5,
            "required": true,
            "type": "rating"
          },
          {
            "help": "Rate the support services provided (e.g., advising, tutoring)",
            "id": "f_22",
            "label": "Support Services",
            "max_rating": 5,
            "required": true,
            "type": "rating"
          },
          {
            "help": "Provide any suggestions for improving the program or courses",
            "id": "f_23",
            "label": "Suggestions for Improvement",
            "placeholder": "Enter your suggestions here",
            "required": false,
            "type": "long_text"
          },
          {
            "help": "",
            "id": "f_24",
            "label": "Would you recommend this program to others?",
            "options": [
              "Yes",
              "No"
            ],
            "required": true,
            "type": "checkbox"
          },
          {
            "help": "Any other comments or feedback you would like to share",
            "id": "f_25",
            "label": "Additional Comments",
            "placeholder": "Enter your comments here",
            "required": false,
            "type": "long_text"
          }
        ],
        "id": "page_2",
        "title": "General Feedback"
      }
    ],
    "settings": {
      "confirmation_message": "Thank you for your feedback! We appreciate your input.",
      "is_published": true,
      "notify_email": "",
      "notify_on_submit": false,
      "redirect_url": "",
      "show_progress": true
    },
    "theme": {
      "accent_color": "#0066CC",
      "bg_color": "#F8F9FA",
      "button_text": "Submit",
      "card_color": "#FFFFFF",
      "cover_image": "",
      "font": "DM Sans",
      "header_color": "#003366",
      "text_color": "#212529"
    },
    "created_at": "2026-04-02T09:02:46.680000",
    "updated_at": "2026-04-02T09:03:23.262000",
    "response_count": 0,
    "responses": []
  },
  {
    "_id": "69d4fbcde0adad724f545e6f",
    "user_id": "69cbaf893e4b965c3ac9bf4f",
    "title": "Expert Nomination Form for Academic Committee",
    "description": "Nominate an expert for consideration in the academic committee. Please provide detailed information about the nominee's qualifications and contributions.",
    "slug": "vk7RJ5_TIHU",
    "pages": [
      {
        "fields": [
          {
            "help": "Enter the full name of the nominee as it appears in academic records.",
            "id": "f_1",
            "label": "Full Name of Nominee",
            "placeholder": "e.g., Dr. Jane Smith",
            "required": true,
            "type": "short_text"
          },
          {
            "help": "Enter the nominee's academic or professional title.",
            "id": "f_2",
            "label": "Academic Title",
            "placeholder": "e.g., Professor, PhD",
            "required": true,
            "type": "short_text"
          },
          {
            "help": "Provide the nominee's primary email address for contact.",
            "id": "f_3",
            "label": "Email Address",
            "placeholder": "e.g., jane.smith@university.edu",
            "required": true,
            "type": "email"
          },
          {
            "help": "Name of the institution where the nominee is currently affiliated.",
            "id": "f_4",
            "label": "Affiliated Institution",
            "placeholder": "e.g., Harvard University",
            "required": true,
            "type": "short_text"
          },
          {
            "help": "Summarize the nominee's academic background, key achievements, and contributions to the field.",
            "id": "f_5",
            "label": "Brief Biography (500 words max)",
            "placeholder": "Include education, publications, awards, and relevant experience.",
            "required": true,
            "type": "long_text"
          }
        ],
        "id": "page_1",
        "title": "Nominee Information"
      },
      {
        "fields": [
          {
            "help": "List the nominee's primary areas of expertise relevant to the committee.",
            "id": "f_6",
            "label": "Areas of Expertise",
            "placeholder": "e.g., Quantum Physics, Educational Policy, Climate Science",
            "required": true,
            "type": "long_text"
          },
          {
            "help": "Describe the nominee's most significant contributions to their field (e.g., publications, projects, innovations).",
            "id": "f_7",
            "label": "Key Contributions",
            "placeholder": "Include specific examples with dates if possible.",
            "required": true,
            "type": "long_text"
          },
          {
            "help": "Select how the nominee's expertise aligns with the committee's focus areas.",
            "id": "f_8",
            "label": "Relevance to Committee",
            "options": [
              "Highly Relevant",
              "Moderately Relevant",
              "Somewhat Relevant",
              "Not Relevant"
            ],
            "required": true,
            "type": "dropdown"
          },
          {
            "help": "Rate the overall impact of the nominee's contributions to their field.",
            "id": "f_9",
            "label": "Impact of Contributions",
            "max_rating": 10,
            "required": true,
            "type": "rating"
          }
        ],
        "id": "page_2",
        "title": "Expertise and Contributions"
      },
      {
        "fields": [
          {
            "help": "Attach relevant documents such as CV, publications, or letters of recommendation (PDF or Word format, max 10MB).",
            "id": "f_10",
            "label": "Upload Supporting Documents",
            "required": false,
            "type": "file"
          },
          {
            "help": "Provide any additional information or context that may support the nomination.",
            "id": "f_11",
            "label": "Additional Comments",
            "placeholder": "e.g., Letters of support, specific achievements",
            "required": false,
            "type": "long_text"
          }
        ],
        "id": "page_3",
        "title": "Supporting Documents"
      }
    ],
    "settings": {
      "confirmation_message": "Thank you for submitting the nomination. The committee will review the details and contact you if further information is required.",
      "is_published": true,
      "notify_email": "",
      "notify_on_submit": false,
      "presentation_style": "web",
      "redirect_url": "",
      "show_progress": true
    },
    "theme": {
      "accent_color": "#2E86C1",
      "bg_color": "#F8F9FA",
      "button_text": "Submit Nomination",
      "card_color": "#FFFFFF",
      "cover_image": "",
      "font": "DM Sans",
      "header_color": "#1A1A2E",
      "text_color": "#212529"
    },
    "created_at": "2026-04-07T12:42:53.199000",
    "updated_at": "2026-04-07T12:43:43.120000",
    "response_count": 0,
    "responses": []
  },
  {
    "_id": "69d6295be0adad724f545e70",
    "user_id": "69cbaf893e4b965c3ac9bf4f",
    "title": "Mental Health Awareness Survey",
    "description": "Your participation helps us understand mental health awareness and improve support systems.",
    "slug": "26cD_U6Fhrs",
    "pages": [
      {
        "fields": [
          {
            "help": "Please enter your age in years",
            "id": "f_1",
            "label": "Age",
            "placeholder": "e.g., 25",
            "required": true,
            "type": "short_text"
          },
          {
            "help": "Select the option that best describes you",
            "id": "f_2",
            "label": "Gender",
            "options": [
              "Male",
              "Female",
              "Non-binary",
              "Other",
              "Prefer not to say"
            ],
            "required": true,
            "type": "dropdown"
          },
          {
            "help": "Select the highest level you have completed",
            "id": "f_3",
            "label": "Highest level of education completed",
            "options": [
              "High school or equivalent",
              "Some college, no degree",
              "Associate degree",
              "Bachelor's degree",
              "Master's degree",
              "Doctorate or professional degree",
              "Other"
            ],
            "required": true,
            "type": "dropdown"
          }
        ],
        "id": "page_1",
        "title": "Demographics"
      },
      {
        "fields": [
          {
            "help": "Select the most accurate option",
            "id": "f_4",
            "label": "Have you ever received a diagnosis of a mental health condition?",
            "options": [
              "Yes",
              "No",
              "Not sure"
            ],
            "required": true,
            "type": "radio"
          },
          {
            "help": "Check all that apply",
            "id": "f_5",
            "label": "Which of the following mental health conditions have you heard of? (Select all that apply)",
            "options": [
              "Depression",
              "Anxiety",
              "Bipolar disorder",
              "Schizophrenia",
              "PTSD",
              "OCD",
              "Eating disorders",
              "ADHD",
              "None of the above"
            ],
            "required": false,
            "type": "checkbox"
          },
          {
            "help": "Rate your confidence on a scale from 1 (Not confident at all) to 5 (Very confident)",
            "id": "f_6",
            "label": "How confident do you feel in recognizing signs of mental health issues in others?",
            "max_rating": 5,
            "required": true,
            "type": "rating"
          }
        ],
        "id": "page_2",
        "title": "Mental Health Awareness"
      },
      {
        "fields": [
          {
            "help": "Select the most accurate option",
            "id": "f_7",
            "label": "Have you ever sought help for a mental health concern?",
            "options": [
              "Yes",
              "No",
              "Not sure"
            ],
            "required": true,
            "type": "radio"
          },
          {
            "help": "Select all that apply",
            "id": "f_8",
            "label": "Where did you seek help? (Select all that apply)",
            "options": [
              "Family doctor/GP",
              "Mental health professional (e.g., psychologist, psychiatrist)",
              "Support group",
              "Online resources",
              "Friends or family",
              "I have not sought help",
              "Other"
            ],
            "required": false,
            "type": "dropdown"
          },
          {
            "help": "Describe any challenges you have encountered",
            "id": "f_9",
            "label": "What barriers, if any, have you faced in accessing mental health support?",
            "placeholder": "e.g., Cost, stigma, lack of awareness...",
            "required": false,
            "type": "long_text"
          }
        ],
        "id": "page_3",
        "title": "Support and Resources"
      }
    ],
    "settings": {
      "confirmation_message": "Thank you for participating in our Mental Health Awareness Survey! Your responses are valuable to us.",
      "is_published": true,
      "notify_email": "",
      "notify_on_submit": false,
      "redirect_url": "",
      "show_progress": true,
      "presentation_style": "web"
    },
    "theme": {
      "accent_color": "#4A90E2",
      "bg_color": "#F8F9FA",
      "button_text": "Submit Survey",
      "card_color": "#FFFFFF",
      "cover_image": "",
      "font": "DM Sans",
      "header_color": "#1A1A2E",
      "text_color": "#212529"
    },
    "created_at": "2026-04-08T10:09:31.773000",
    "updated_at": "2026-04-08T10:10:01.521000",
    "response_count": 0,
    "responses": []
  },
  {
    "_id": "69d766538432bee366277445",
    "user_id": "69cbaf893e4b965c3ac9bf4f",
    "title": "Student Feedback Survey - Semester End",
    "description": "A comprehensive survey to gather student feedback on courses, instructors, facilities, and overall experience for semester improvement.",
    "slug": "tjX3MEouLzQ",
    "pages": [
      {
        "fields": [
          {
            "help": "Enter your full name as per records.",
            "id": "f_1",
            "label": "Full Name",
            "required": true,
            "type": "short_text"
          },
          {
            "help": "Enter your student ID number.",
            "id": "f_11",
            "label": "Student ID",
            "required": true,
            "type": "short_text"
          },
          {
            "help": "Select the semester you are providing feedback for.",
            "id": "f_2",
            "label": "Which semester did you complete?",
            "options": [
              "Fall 2023",
              "Spring 2024",
              "Summer 2024",
              "Fall 2024"
            ],
            "required": true,
            "type": "dropdown"
          },
          {
            "help": "Upload a recent passport-sized photo.",
            "id": "f_12",
            "label": "Upload Your Photo",
            "required": false,
            "type": "file"
          },
          {
            "help": "Rate your overall satisfaction.",
            "id": "f_3",
            "label": "Overall, how satisfied were you with this semester?",
            "options": [
              "Very Dissatisfied",
              "Dissatisfied",
              "Neutral",
              "Satisfied",
              "Very Satisfied"
            ],
            "required": true,
            "type": "dropdown"
          },
          {
            "help": "Share your positive experiences.",
            "id": "f_4",
            "label": "What did you like most about this semester?",
            "required": false,
            "type": "long_text"
          }
        ],
        "id": "page_1",
        "title": "Student Details & Course Experience"
      },
      {
        "fields": [
          {
            "help": "Select the option that best describes your experience.",
            "id": "f_5",
            "label": "How would you rate the teaching quality of your instructors?",
            "options": [
              "Excellent",
              "Good",
              "Average",
              "Poor",
              "Very Poor"
            ],
            "required": true,
            "type": "dropdown"
          },
          {
            "help": "Provide constructive feedback if needed.",
            "id": "f_6",
            "label": "Do you have any specific feedback for your instructors? (e.g., teaching methods, communication)",
            "required": false,
            "type": "long_text"
          }
        ],
        "id": "page_2",
        "title": "Instructor Feedback"
      },
      {
        "fields": [
          {
            "help": "1 = Very Easy, 5 = Very Difficult",
            "id": "f_7",
            "label": "How would you rate the difficulty of your courses?",
            "max_rating": 5,
            "required": true,
            "type": "rating"
          },
          {
            "help": "Share your thoughts on the course load.",
            "id": "f_8",
            "label": "Do you feel the workload was manageable?",
            "required": false,
            "type": "long_text"
          }
        ],
        "id": "page_3",
        "title": "Course Content & Workload"
      },
      {
        "fields": [
          {
            "help": "Select all that apply.",
            "id": "f_9",
            "label": "Which facilities did you find most helpful?",
            "options": [
              "Library",
              "Laboratories",
              "Online Resources",
              "Student Support Services",
              "None"
            ],
            "required": false,
            "type": "checkbox"
          },
          {
            "help": "Share any unmet needs.",
            "id": "f_10",
            "label": "What additional support do you wish you had during the semester?",
            "required": false,
            "type": "long_text"
          }
        ],
        "id": "page_4",
        "title": "Facilities & Support"
      },
      {
        "fields": [
          {
            "help": "Your input is valuable to us.",
            "id": "f_13",
            "label": "Any other feedback or suggestions for improvement?",
            "required": false,
            "type": "long_text"
          }
        ],
        "id": "page_5",
        "title": "Final Thoughts"
      }
    ],
    "settings": {
      "confirmation_message": "Thank you for your valuable feedback! Your responses will help us improve future semesters.",
      "is_published": true,
      "notify_email": "",
      "notify_on_submit": false,
      "redirect_url": "",
      "show_progress": true
    },
    "theme": {
      "accent_color": "#0066CC",
      "bg_color": "#EEF4FF",
      "button_text": "Submit Feedback",
      "card_color": "#FFFFFF",
      "cover_image": "",
      "font": "Inter",
      "header_color": "#003366",
      "text_color": "#1A2A3A"
    },
    "created_at": "2026-04-09T08:41:55.184000",
    "updated_at": "2026-04-09T08:44:25.737000",
    "response_count": 0,
    "responses": []
  },
  {
    "_id": "69d7674d8432bee366277446",
    "user_id": "69cbaf893e4b965c3ac9bf4f",
    "title": "New Quiz",
    "description": "",
    "slug": "pfcFWCFk6W4",
    "pages": [
      {
        "fields": [
          {
            "id": "f_1775724369873",
            "type": "quiz_tf",
            "label": "True or False?",
            "help": "",
            "required": false,
            "placeholder": "",
            "options": [
              "True",
              "False"
            ],
            "correct_answer": "True",
            "points": 1
          },
          {
            "id": "f_1775724371754",
            "type": "quiz_mc",
            "label": "Quiz Question",
            "help": "",
            "required": false,
            "placeholder": "",
            "options": [
              "Option A",
              "Option B",
              "Option C",
              "Option D"
            ],
            "correct_answer": "Option A",
            "points": 1
          },
          {
            "id": "f_1775724374391",
            "type": "checkbox_grid",
            "label": "Checkbox Grid",
            "help": "",
            "required": false,
            "placeholder": "",
            "rows": [
              "Row 1",
              "Row 2"
            ],
            "cols": [
              "Col 1",
              "Col 2",
              "Col 3"
            ]
          },
          {
            "id": "f_1775724380311",
            "type": "dropdown",
            "label": "Dropdown",
            "help": "",
            "required": false,
            "placeholder": "",
            "options": [
              "Option 1",
              "Option 2",
              "Option 3"
            ]
          }
        ],
        "id": "page_1",
        "title": "Page 1"
      }
    ],
    "settings": {
      "confirmation_message": "Thank you for your response!",
      "is_published": false,
      "notify_email": "",
      "notify_on_submit": false,
      "presentation_style": "form",
      "redirect_url": "",
      "show_progress": true
    },
    "theme": {
      "accent_color": "#FF8C00",
      "bg_color": "#F8F9FA",
      "button_text": "Submit",
      "card_color": "#FFFFFF",
      "cover_image": "",
      "font": "DM Sans",
      "header_color": "#1A1A2E",
      "header_style": "gradient",
      "text_color": "#212529"
    },
    "created_at": "2026-04-09T08:46:05.249000",
    "updated_at": "2026-04-09T08:46:21.255000",
    "response_count": 0,
    "responses": []
  },
  {
    "_id": "69d768348432bee366277447",
    "user_id": "69cbaf893e4b965c3ac9bf4f",
    "title": "University Seminar Registration",
    "description": "Register your attendance for the upcoming university seminar.",
    "slug": "rdz_NsRvAiM",
    "pages": [
      {
        "fields": [
          {
            "help": "Please enter your full name as it appears on official documents.",
            "id": "f_1",
            "label": "Full Name",
            "placeholder": "e.g., John Doe",
            "required": true,
            "type": "short_text"
          },
          {
            "help": "A valid university or personal email address.",
            "id": "f_2",
            "label": "Email Address",
            "placeholder": "e.g., john.doe@university.edu",
            "required": true,
            "type": "email"
          },
          {
            "help": "Include country code if outside the university's region.",
            "id": "f_3",
            "label": "Phone Number",
            "placeholder": "e.g., +1 123-456-7890",
            "required": false,
            "type": "phone"
          },
          {
            "help": "Select your current academic year.",
            "id": "f_4",
            "label": "Academic Year",
            "options": [
              "Freshman",
              "Sophomore",
              "Junior",
              "Senior",
              "Graduate Student",
              "PhD Candidate",
              "Other"
            ],
            "required": true,
            "type": "dropdown"
          },
          {
            "help": "Select one option.",
            "id": "f_5",
            "label": "Are you a member of the organizing department?",
            "options": [
              "Yes",
              "No"
            ],
            "required": true,
            "type": "radio"
          }
        ],
        "id": "page_1",
        "title": "Personal Information"
      },
      {
        "fields": [
          {
            "help": "Select the seminar you wish to attend.",
            "id": "f_6",
            "label": "Seminar Topic",
            "options": [
              "AI in Modern Healthcare",
              "Sustainable Energy Solutions",
              "Cybersecurity in the Digital Age",
              "Neuroscience Breakthroughs",
              "Other (Specify Below)"
            ],
            "required": true,
            "type": "dropdown"
          },
          {
            "help": "Specify the seminar topic if 'Other' was selected above.",
            "id": "f_7",
            "label": "Other Topic (if applicable)",
            "placeholder": "Enter your topic here",
            "required": false,
            "type": "long_text"
          },
          {
            "help": "Select your preferred date to attend the seminar.",
            "id": "f_8",
            "label": "Preferred Date",
            "required": true,
            "type": "date"
          },
          {
            "help": "Select your preferred time slot for the seminar.",
            "id": "f_9",
            "label": "Preferred Time Slot",
            "options": [
              "9:00 AM - 11:00 AM",
              "11:00 AM - 1:00 PM",
              "1:00 PM - 3:00 PM",
              "3:00 PM - 5:00 PM"
            ],
            "required": true,
            "type": "time"
          }
        ],
        "id": "page_2",
        "title": "Seminar Details"
      },
      {
        "fields": [
          {
            "help": "Select any dietary restrictions for catering purposes.",
            "id": "f_10",
            "label": "Dietary Restrictions",
            "options": [
              "Vegetarian",
              "Vegan",
              "Gluten-Free",
              "Halal",
              "Kosher",
              "Nut Allergy",
              "Other (Specify Below)"
            ],
            "required": false,
            "type": "checkbox"
          },
          {
            "help": "Specify any other dietary restrictions not listed above.",
            "id": "f_11",
            "label": "Other Dietary Restrictions",
            "placeholder": "Enter your dietary restrictions here",
            "required": false,
            "type": "long_text"
          },
          {
            "help": "Rate your likelihood on a scale from 1 to 5.",
            "id": "f_12",
            "label": "How likely are you to recommend this seminar to a colleague?",
            "max_rating": 5,
            "required": false,
            "type": "rating"
          }
        ],
        "id": "page_3",
        "title": "Additional Information"
      }
    ],
    "settings": {
      "confirmation_message": "Thank you for registering! You will receive a confirmation email shortly with further details.",
      "is_published": true,
      "notify_email": "events@university.edu",
      "notify_on_submit": true,
      "presentation_style": "web",
      "redirect_url": "",
      "show_progress": true
    },
    "theme": {
      "accent_color": "#2563EB",
      "bg_color": "#F8F9FA",
      "button_text": "Register Now",
      "card_color": "#FFFFFF",
      "cover_image": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80",
      "font": "DM Sans",
      "header_color": "#1A1A2E",
      "text_color": "#212529"
    },
    "created_at": "2026-04-09T08:49:56.690000",
    "updated_at": "2026-04-09T08:53:14.524000",
    "response_count": 1,
    "responses": [
      {
        "_id": "69d769378432bee366277448",
        "form_id": "69d768348432bee366277447",
        "data": {
          "f_1": "SH",
          "f_2": "a@b.com",
          "f_3": "123456789",
          "f_4": "Freshman",
          "f_5": "Yes",
          "f_6": "AI in Modern Healthcare",
          "f_7": ";lm",
          "f_8": "2026-04-01",
          "f_9": "12:12",
          "f_10": [
            "Vegetarian",
            "Vegan",
            "Gluten-Free",
            "Halal",
            "Kosher",
            "Nut Allergy",
            "Other (Specify Below)"
          ],
          "f_11": "none",
          "f_12": "5"
        },
        "respondent_ip": "106.51.79.124",
        "user_id": null,
        "submitted_at": "2026-04-09T08:54:15.593000"
      }
    ]
  }
]; _NL=[
  {
    "_id": "69d77bca8432bee36627744a",
    "user_id": "69cbaf893e4b965c3ac9bf4f",
    "title": "India\u2019s AI Revolution in Schools",
    "subtitle": "AI to Enter Every Indian School from Grade 3",
    "footer": "Ministry of Education \u00b7 PIB \u00b7 CBSE \u00b7 NCERT \u00b7 Unsubscribe",
    "blocks": [
      {
        "content": {
          "level": "h2",
          "text": "<font face=\"DM Sans\" style=\"font-size: 23px;\">AI to Enter Every Indian School from Grade 3</font>"
        },
        "id": "b1",
        "type": "heading"
      },
      {
        "content": {
          "html": "<p dir=\"ltr\" style=\"line-height:1.2;margin-top:14pt;margin-bottom:14pt;\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">India is taking a decisive step toward embedding AI into mainstream schooling. Starting 2026\u201327, a mandatory AI curriculum will be introduced from Grade 3 upward, aligned with NEP 2020 and the National Curriculum Framework (NCF-SE) 2023.</span></p><p><span id=\"docs-internal-guid-8cff4c8a-7fff-7fc5-03d0-6cb4b61c585f\"><span style=\"font-size: 12pt; font-family: &quot;Times New Roman&quot;, serif; color: rgb(0, 0, 0); background-color: transparent; font-variant-numeric: normal; font-variant-east-asian: normal; font-variant-alternates: normal; font-variant-position: normal; font-variant-emoji: normal; vertical-align: baseline; white-space-collapse: preserve;\">The Ministry of Education has already integrated AI into school curricula through CBSE and NCERT from Grade 9, with CBSE offering a 15-hour AI skill module from Class VI and AI as an optional subject in Classes IX\u2013XII. </span><a href=\"https://www.pib.gov.in/PressReleasePage.aspx?PRID=2234853&amp;reg=3&amp;lang=1\" style=\"text-decoration-line: none;\"><span style=\"font-size: 12pt; font-family: &quot;Times New Roman&quot;, serif; color: rgb(0, 0, 255); background-color: transparent; font-variant-numeric: normal; font-variant-east-asian: normal; font-variant-alternates: normal; font-variant-position: normal; font-variant-emoji: normal; text-decoration-line: underline; text-decoration-skip-ink: none; vertical-align: baseline; white-space-collapse: preserve;\">Press Information Bureau</span></a><span style=\"font-size: 12pt; font-family: &quot;Times New Roman&quot;, serif; color: rgb(0, 0, 0); background-color: transparent; font-variant-numeric: normal; font-variant-east-asian: normal; font-variant-alternates: normal; font-variant-position: normal; font-variant-emoji: normal; vertical-align: baseline; white-space-collapse: preserve;\"> The new mandate extends this ambition significantly downward in age. Learning materials, teacher guides, and digital content were to be completed by December 2025, with educators undergoing structured, grade-specific training through NISHTHA and other recognised institutions. </span><a href=\"https://coingeek.com/india-to-introduce-ai-curriculum-in-all-schools-by-2026/\" style=\"text-decoration-line: none;\"><span style=\"font-size: 12pt; font-family: &quot;Times New Roman&quot;, serif; color: rgb(0, 0, 255); background-color: transparent; font-variant-numeric: normal; font-variant-east-asian: normal; font-variant-alternates: normal; font-variant-position: normal; font-variant-emoji: normal; text-decoration-line: underline; text-decoration-skip-ink: none; vertical-align: baseline; white-space-collapse: preserve;\">CoinGeek</span></a></span></p>"
        },
        "id": "b2",
        "type": "text"
      },
      {
        "content": {
          "author": "",
          "text": "Why it matters:&nbsp; Future university students will arrive with basic AI literacy\u2014higher education must level up."
        },
        "id": "b17757349538021",
        "type": "quote"
      },
      {
        "content": {
          "level": "h2",
          "text": "&nbsp;Google DeepMind launcE5Yhes major India education partnership"
        },
        "id": "b17757350792262",
        "type": "heading"
      },
      {
        "content": {
          "level": "h2",
          "text": "Section Heading4EWY"
        },
        "id": "b17757362908770",
        "type": "heading"
      },
      {
        "content": {
          "level": "h2",
          "text": "Section Heading"
        },
        "id": "b17758109855031",
        "type": "heading"
      },
      {
        "content": {
          "level": "h2",
          "text": "Section Heading"
        },
        "id": "b17758109946652",
        "type": "heading"
      },
      {
        "content": {},
        "id": "b17758109979133",
        "type": "divider"
      },
      {
        "content": {
          "author": "",
          "text": "An inspiring quote here.REY"
        },
        "id": "b17758110006814",
        "type": "quote"
      },
      {
        "content": {
          "caption": "",
          "gif_align": "center",
          "gif_width": "100%",
          "url": ""
        },
        "id": "b17758115261857",
        "type": "gif"
      },
      {
        "content": {
          "alt": "",
          "caption": "",
          "url": "/static/nl_uploads/image_f2948188bfa94ad8b757817891fc6c17.jpg"
        },
        "id": "b17758134617860",
        "type": "image"
      }
    ],
    "theme": {
      "_hdr_had_base64": true,
      "_logo_had_base64": true,
      "accent_color": "#8e2de2",
      "bg_color": "#ffffff",
      "header_color": "#1A1A2E",
      "header_image": "",
      "logo_align": "center",
      "logo_height": 50,
      "logo_radius": 6,
      "logo_text": "\u25c8 Draftspace",
      "logo_url": "",
      "logo_width": 140
    },
    "created_at": "2026-04-09T10:13:30.636000",
    "updated_at": "2026-04-10T11:01:00.366000",
    "last_sent": "2026-04-10 08:42:52.411000",
    "send_count": 1
  },
  {
    "_id": "69d7824d89f6d332325c6fc3",
    "user_id": "69cbaf893e4b965c3ac9bf4f",
    "title": "AI in Every Indian Classroom by 2026",
    "subtitle": "A New Era of Learning Begins",
    "footer": "Ministry of Education \u00b7 Unsubscribe",
    "blocks": [
      {
        "content": {
          "level": "h2",
          "text": "Welcome to Our Newsletter"
        },
        "id": "b177573131850538",
        "type": "heading"
      },
      {
        "content": {
          "html": "<p>Here's what's happening this month.</p>"
        },
        "id": "b177573131850539",
        "type": "text"
      },
      {
        "content": {
          "alt": "",
          "url": ""
        },
        "id": "b177573131850540",
        "type": "image"
      },
      {
        "content": {
          "author": "Aristotle",
          "text": "Excellence is not an act but a habit."
        },
        "id": "b177573131850541",
        "type": "quote"
      },
      {
        "content": {
          "left": "<strong>\ud83d\udccc Highlight 1</strong><p>Description here.</p>",
          "right": "<strong>\ud83d\udccc Highlight 2</strong><p>Description here.</p>"
        },
        "id": "b177573131850542",
        "type": "2col"
      },
      {
        "content": {
          "color": "#FF8C00",
          "text": "Read More \u2192",
          "url": "#"
        },
        "id": "b177573131850543",
        "type": "cta"
      }
    ],
    "theme": {
      "accent_color": "#FF8C00",
      "bg_color": "#ffffff",
      "header_color": "#1A1A2E",
      "header_image": "",
      "logo_align": "center",
      "logo_height": 50,
      "logo_radius": 6,
      "logo_text": "\u25c8 Draftspace",
      "logo_url": "",
      "logo_width": 140
    },
    "created_at": "2026-04-09T10:41:17.593000",
    "updated_at": "2026-04-10T09:07:09.644000"
  },
  {
    "_id": "69d8964fec2d4b5682d434bd",
    "user_id": "69cbaf893e4b965c3ac9bf4f",
    "title": "India\u2019s AI Revolution in Schools",
    "subtitle": "",
    "footer": "Jain (Deemed-to-be-University) Head Office",
    "blocks": [
      {
        "content": {
          "level": "h2",
          "text": "<div style=\"text-align: center;\"><span style=\"background-color: transparent; font-size: 22px; color: rgb(0, 0, 0); font-family: &quot;Times New Roman&quot;, serif; white-space-collapse: preserve;\">AI to </span><font color=\"#e24a08\" style=\"font-size: 0.92rem;\"><span style=\"font-size: 22px; background-color: transparent; font-family: &quot;Times New Roman&quot;, serif; white-space-collapse: preserve;\">E</span><span style=\"font-size: 22px; background-color: transparent; font-family: &quot;Times New Roman&quot;, serif; white-space-collapse: preserve;\">nter every Indian scho</span><span style=\"background-color: transparent; font-family: &quot;Times New Roman&quot;, serif; white-space-collapse: preserve;\"><font style=\"font-size: 23px;\">o</font></span><span style=\"font-size: 22px; background-color: transparent; font-family: &quot;Times New Roman&quot;, serif; white-space-collapse: preserve;\">l</span><span style=\"font-size: 22px; background-color: transparent; font-family: &quot;Times New Roman&quot;, serif; white-space-collapse: preserve;\"> </span></font><span style=\"background-color: transparent; font-size: 22px; color: rgb(0, 0, 0); font-family: &quot;Times New Roman&quot;, serif; white-space-collapse: preserve;\">from Grade 3</span></div>"
        },
        "id": "b17758040953170",
        "type": "heading"
      },
      {
        "content": {
          "alt": "",
          "caption": "",
          "url": "/static/nl_uploads/image_1b5096695f194107923d966043b332e3.png"
        },
        "id": "b17758181052680",
        "type": "image"
      },
      {
        "content": {
          "html": "<p dir=\"ltr\" style=\"text-align: justify; line-height: 1.2; margin-top: 14pt; margin-bottom: 14pt;\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">India is taking a decisive step toward embedding AI into mainstream schooling. Starting 2026\u201327, a mandatory AI curriculum will be introduced from Grade 3 upward, aligned with NEP 2020 and the National Curriculum Framework (NCF-SE) 2023.</span></p><p dir=\"ltr\" style=\"text-align: justify; line-height: 1.2; margin-top: 14pt; margin-bottom: 14pt;\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">The Ministry of Education has already integrated AI into school curricula through CBSE and NCERT from Grade 9, with CBSE offering a 15-hour AI skill module from Class VI and AI as an optional subject in Classes IX\u2013XII. </span><a href=\"https://www.pib.gov.in/PressReleasePage.aspx?PRID=2234853&amp;reg=3&amp;lang=1\" style=\"text-decoration:none;\" target=\"_blank\" rel=\"noopener\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#0000ff;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:underline;-webkit-text-decoration-skip:none;text-decoration-skip-ink:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">Press Information Bureau</span></a><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\"> The new mandate extends this ambition significantly downward in age. Learning materials, teacher guides, and digital content were to be completed by December 2025, with educators undergoing structured, grade-specific training through NISHTHA and other recognised institutions. </span><a href=\"https://coingeek.com/india-to-introduce-ai-curriculum-in-all-schools-by-2026/\" style=\"text-decoration:none;\" target=\"_blank\" rel=\"noopener\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#0000ff;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:underline;-webkit-text-decoration-skip:none;text-decoration-skip-ink:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">CoinGeek</span></a></p><p dir=\"ltr\" style=\"text-align: justify; line-height: 1.2; margin-top: 14pt; margin-bottom: 14pt;\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">NCERT has also used AI and ML to translate Grade 1\u20132 textbooks into 22 Indian languages </span><a href=\"https://www.pib.gov.in/PressReleasePage.aspx?PRID=2234853&amp;reg=3&amp;lang=1\" style=\"text-decoration:none;\" target=\"_blank\" rel=\"noopener\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#0000ff;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:underline;-webkit-text-decoration-skip:none;text-decoration-skip-ink:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">Press Information Bureau</span></a><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\"> a practical demonstration of the technology's value for inclusive education at scale.</span></p>"
        },
        "id": "b17758041819891",
        "type": "text"
      },
      {
        "content": {
          "author": "",
          "text": "Future students will arrive AI-ready\u2014universities must build ahead, not start over"
        },
        "id": "b17758146112276",
        "type": "quote"
      },
      {
        "content": {
          "level": "h2",
          "text": "<div style=\"text-align: center;\"><span style=\"background-color: transparent; font-family: &quot;Times New Roman&quot;, serif; white-space-collapse: preserve;\"><font style=\"font-size: 23px;\"><font color=\"#000000\">&nbsp;</font><font color=\"#e24a08\">Google DeepMind </font><font color=\"#000000\">launches major India education partnership</font></font></span></div>"
        },
        "id": "b17758146316757",
        "type": "heading"
      },
      {
        "id": "b17760590446890",
        "type": "image",
        "content": {
          "url": "/static/nl_uploads/image_5b516e32984949d99ae34da339d15aa9.png",
          "alt": "",
          "caption": ""
        }
      },
      {
        "content": {
          "html": "<p dir=\"ltr\" style=\"text-align: justify; line-height: 1.2; margin-top: 14pt; margin-bottom: 14pt;\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">Google DeepMind announced a new partnership with Indian government bodies and institutions through its National Partnerships for AI initiative, focusing on science, education, and public services. </span><a href=\"https://deepmind.google/blog/accelerating-discovery-in-india-through-ai-powered-science-and-education/\" style=\"text-decoration:none;\" target=\"_blank\" rel=\"noopener\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#0000ff;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:underline;-webkit-text-decoration-skip:none;text-decoration-skip-ink:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">Google DeepMind</span></a></p><p dir=\"ltr\" style=\"text-align: justify; line-height: 1.2; margin-top: 14pt; margin-bottom: 14pt;\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">The scale is substantial. An \u20b985 crore (nearly $10 million) Google.org grant was announced for Wadhwani AI to scale adaptive learning for 75 million students, 1.8 million educators, and 1 million early-career professionals by December 2027. </span><a href=\"https://blog.google/intl/en-in/powering-indias-next-generation-with-the-science-of-learning/\" style=\"text-decoration:none;\" target=\"_blank\" rel=\"noopener\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#0000ff;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:underline;-webkit-text-decoration-skip:none;text-decoration-skip-ink:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">Google</span></a><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\"> Google DeepMind is also working with Atal Tinkering Labs covering over 10,000 schools and 11 million students \u2014 to integrate robotics, coding, and Gemini-based AI assistants into learning environments and teacher workflows. </span><a href=\"https://news.careers360.com/google-deepmind-anrf-ai-research-education-india-impact-challenge-students-teachers/amp\" style=\"text-decoration:none;\" target=\"_blank\" rel=\"noopener\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#0000ff;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:underline;-webkit-text-decoration-skip:none;text-decoration-skip-ink:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">Careers360</span></a></p><p dir=\"ltr\" style=\"text-align: justify; line-height: 1.2; margin-top: 14pt; margin-bottom: 14pt;\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">For research, the partnership with the Anusandhan National Research Foundation (ANRF) will provide Indian researchers and early-career scientists access to frontier AI tools, supporting hackathons, mentorship, and training. </span><a href=\"https://blog.google/intl/en-in/company-news/accelerating-discovery-in-india-through-ai-powered-science-and-education/\" style=\"text-decoration:none;\" target=\"_blank\" rel=\"noopener\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#0000ff;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:underline;-webkit-text-decoration-skip:none;text-decoration-skip-ink:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">Google</span></a><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\"> A $2 million founding contribution has also been made to establish a new Indic Language Technologies Research Hub at IIT Bombay. </span><a href=\"https://blog.google/intl/en-in/company-news/accelerating-discovery-in-india-through-ai-powered-science-and-education/\" style=\"text-decoration:none;\" target=\"_blank\" rel=\"noopener\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#0000ff;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:underline;-webkit-text-decoration-skip:none;text-decoration-skip-ink:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">Google</span></a></p><p><span id=\"docs-internal-guid-37ddaed6-7fff-91b7-ba87-d69da19ce0fd\"></span></p><p dir=\"ltr\" style=\"text-align: justify; line-height: 1.2; margin-top: 14pt; margin-bottom: 14pt;\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">For departments engaged in language studies, regional research, or applied sciences, these partnerships represent concrete collaboration opportunities. More broadly, they signal that global technology organisations are making long-term structural commitments to Indian academia something institutional strategy should begin to account for.</span></p>"
        },
        "id": "b17758146459979",
        "type": "text"
      },
      {
        "content": {
          "author": "",
          "text": "Global AI leaders are investing at scale in Indian education\u2014universities must position themselves to collaborate, not observe"
        },
        "id": "b177581465058610",
        "type": "quote"
      },
      {
        "content": {
          "level": "h2",
          "text": "<div style=\"text-align: center;\"><span style=\"font-size: 21px; background-color: transparent; font-family: &quot;Times New Roman&quot;, serif; white-space-collapse: preserve;\"><font color=\"#e54c0b\">&nbsp;EDNXT Bengaluru Summit:</font></span><span style=\"font-size: 21px; background-color: transparent; color: rgb(0, 0, 0); font-family: &quot;Times New Roman&quot;, serif; white-space-collapse: preserve;\"> AI as the defining force for universities</span></div>"
        },
        "id": "b177581469957111",
        "type": "heading"
      },
      {
        "id": "b17760591831212",
        "type": "image",
        "content": {
          "url": "/static/nl_uploads/image_64ee4e88c8d44200bb121b4aee3aa51d.png",
          "alt": "",
          "caption": ""
        }
      },
      {
        "content": {
          "html": "<p dir=\"ltr\" style=\"text-align: justify; line-height: 1.2; margin-top: 14pt; margin-bottom: 14pt;\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">At the EDNXT Bengaluru Summit 2026, organised by The Economic Times Education, policymakers, academic leaders, and industry innovators gathered around the theme \"The Education Transformation: AI, Access &amp; Acceleration,\" exploring how AI-driven transformation and global collaboration are reshaping universities worldwide. </span><a href=\"https://www.isbr.in/blogs/ai-in-higher-education-ednxt-bengaluru-summit-2026/\" style=\"text-decoration:none;\" target=\"_blank\" rel=\"noopener\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#0000ff;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:underline;-webkit-text-decoration-skip:none;text-decoration-skip-ink:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">ISBR Blog</span></a></p><p dir=\"ltr\" style=\"text-align: justify; line-height: 1.2; margin-top: 14pt; margin-bottom: 14pt;\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">Three themes stand out for department heads. First, faculty readiness was identified as a prerequisite for transformation, not an afterthought \u2014 when faculty are empowered with AI-driven teaching tools, they deliver more engaging and effective learning experiences. </span><a href=\"https://www.isbr.in/blogs/ai-in-higher-education-ednxt-bengaluru-summit-2026/\" style=\"text-decoration:none;\" target=\"_blank\" rel=\"noopener\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#0000ff;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:underline;-webkit-text-decoration-skip:none;text-decoration-skip-ink:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">ISBR Blog</span></a><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\"> Second, AI-powered interdisciplinary research was highlighted as expanding innovation boundaries, with universities encouraged to build collaborative ecosystems rather than siloed departmental approaches.</span></p><p dir=\"ltr\" style=\"text-align: justify; line-height: 1.2; margin-top: 14pt; margin-bottom: 14pt;\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">Third, and most pressing, was institutional strategy. The summit reinforced that institutions which successfully integrate AI technologies, digital pedagogy, and global collaborations will lead the next era of academic innovation. </span><a href=\"https://www.isbr.in/blogs/ai-in-higher-education-ednxt-bengaluru-summit-2026/\" style=\"text-decoration:none;\" target=\"_blank\" rel=\"noopener\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#0000ff;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:underline;-webkit-text-decoration-skip:none;text-decoration-skip-ink:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">ISBR Blog</span></a></p><p><span id=\"docs-internal-guid-eaaaf155-7fff-50b2-4459-dc6ff5159fbd\"></span></p><p dir=\"ltr\" style=\"text-align: justify; line-height: 1.2; margin-top: 14pt; margin-bottom: 14pt;\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">The Bengaluru summit serves as a useful benchmark: peer institutions are actively designing AI integration strategies now. Departments that begin mapping AI touchpoints across curricula, research pipelines, and faculty development will be better placed to respond to forthcoming accreditation and regulatory expectations around AI competency.</span></p>"
        },
        "id": "b177581470368513",
        "type": "text"
      },
      {
        "content": {
          "author": "",
          "text": "AI-ready faculty, interdisciplinary research, and clear strategy will define the universities that lead the next era."
        },
        "id": "b177581470429214",
        "type": "quote"
      },
      {
        "content": {
          "level": "h2",
          "text": "<div style=\"text-align: center;\"><font style=\"font-size: 22px;\"><span style=\"background-color: transparent; font-family: &quot;Times New Roman&quot;, serif; white-space-collapse: preserve;\"><font color=\"#e74f0d\" style=\"\">Gemini adds JEE mock tests: </font></span><span style=\"background-color: transparent; color: rgb(0, 0, 0); font-family: &quot;Times New Roman&quot;, serif; white-space-collapse: preserve;\">2 million textbooks go AI-powered</span></font></div>"
        },
        "id": "b177581474311815",
        "type": "heading"
      },
      {
        "id": "b17760591361211",
        "type": "image",
        "content": {
          "url": "/static/nl_uploads/image_b7697d4aba0846d882904831d18c61c6.png",
          "alt": "",
          "caption": ""
        }
      },
      {
        "content": {
          "html": "<p dir=\"ltr\" style=\"text-align: justify; line-height: 1.2; margin-top: 14pt; margin-bottom: 14pt;\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">Two announcements this month illustrated how AI tools are evolving from general assistants into purpose-built academic companions for Indian students.</span></p><p dir=\"ltr\" style=\"text-align: justify; line-height: 1.2; margin-top: 14pt; margin-bottom: 14pt;\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">Google added full-length JEE practice tests in Gemini, grounded in vetted content from Physics Wallah and Careers360. Once students complete a mock test, Gemini provides immediate feedback, highlights strengths and weaknesses, explains correct answers, and generates a customised study plan. </span><a href=\"https://techcrunch.com/2026/01/28/google-turns-gemini-toward-indias-most-competitive-entrance-exam/\" style=\"text-decoration:none;\" target=\"_blank\" rel=\"noopener\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#0000ff;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:underline;-webkit-text-decoration-skip:none;text-decoration-skip-ink:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">TechCrunch</span></a><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\"> India now leads the world in daily Gemini usage for learning, with 74% of Indians believing AI will improve student outcomes. </span><a href=\"https://blog.google/intl/en-in/powering-indias-next-generation-with-the-science-of-learning/\" style=\"text-decoration:none;\" target=\"_blank\" rel=\"noopener\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#0000ff;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:underline;-webkit-text-decoration-skip:none;text-decoration-skip-ink:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">Google</span></a></p><p dir=\"ltr\" style=\"text-align: justify; line-height: 1.2; margin-top: 14pt; margin-bottom: 14pt;\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">At the school level, two million static K-12 textbooks from PM Publishers are being converted into interactive AI experiences, each with a QR-linked Gemini assistant that provides subject-specific summaries and responses. </span><a href=\"https://blog.google/intl/en-in/company-news/accelerating-discovery-in-india-through-ai-powered-science-and-education/\" style=\"text-decoration:none;\" target=\"_blank\" rel=\"noopener\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#0000ff;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:underline;-webkit-text-decoration-skip:none;text-decoration-skip-ink:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">Google</span></a></p><p><span id=\"docs-internal-guid-d1382c74-7fff-eb2f-ba94-2c8b81c12d2f\"></span></p><p dir=\"ltr\" style=\"text-align: justify; line-height: 1.2; margin-top: 14pt; margin-bottom: 14pt;\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">The university-level takeaway is practical: students are already using these tools extensively outside the classroom. Departments that acknowledge this reality \u2014 and update their assessment design, pedagogy, and academic integrity policies accordingly \u2014 will be better prepared than those treating AI tool usage as exceptional. Google has also announced plans with the Ministry of Skill Development to build a national framework for applying AI across vocational and higher education. </span><a href=\"https://techcrunch.com/2026/01/28/google-turns-gemini-toward-indias-most-competitive-entrance-exam/\" style=\"text-decoration:none;\" target=\"_blank\" rel=\"noopener\"><span style=\"font-size:12pt;font-family:'Times New Roman',serif;color:#0000ff;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:underline;-webkit-text-decoration-skip:none;text-decoration-skip-ink:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">TechCrunch</span></a></p>"
        },
        "id": "b177581474485917",
        "type": "text"
      },
      {
        "content": {
          "author": "",
          "text": "AI is already shaping how students learn\u2014universities must adapt their teaching and assessment to match this reality"
        },
        "id": "b177581474653218",
        "type": "quote"
      },
      {
        "content": {},
        "id": "b177581491066021",
        "type": "divider"
      },
      {
        "content": {
          "level": "h2",
          "text": "<div style=\"text-align: center;\"><font style=\"font-weight: 400; font-size: 20px;\" face=\"Times New Roman\"><b style=\"\">Curious if you\u2019re keeping up with the AI revolution? Test your knowledge with our mini quiz.</b></font></div><div style=\"text-align: center;\"><font color=\"#e74f0d\"><span style=\"font-size: 20px; font-family: &quot;Times New Roman&quot;;\">Results will be ann</span><span style=\"font-size: 20px; font-family: &quot;Times New Roman&quot;;\">ounced in the next month newsletter</span></font></div>"
        },
        "id": "b17758206937515",
        "type": "heading"
      },
      {
        "content": {
          "color": "#0b4a9d",
          "text": "TAKE PART IN THE APRIL EDITION QUIZ!",
          "url": "https://forms.gle/XnCneydnh75dtDtH6"
        },
        "id": "b17758155981398",
        "type": "cta"
      },
      {
        "content": {},
        "id": "b177581710796713",
        "type": "divider"
      },
      {
        "content": {
          "bg": "#1A1A2E",
          "color": "#fff",
          "text": "<font color=\"#c2beb7\">March Month Quiz winner</font><span style=\"color: rgb(194, 190, 188); font-family: Verdana; font-size: 17.6px;\">\ud83c\udf89</span><font color=\"#c2beb7\"><br></font><font style=\"\" face=\"Verdana\" color=\"#f7f5f2\">Dr.K.Manivannan&nbsp;</font><div><font style=\"\" face=\"Verdana\" color=\"#f7f5f2\">Department of Information Science and Engineering</font></div>"
        },
        "id": "b177581508565325",
        "type": "hdr"
      },
      {
        "content": {
          "html": "<p style=\"text-align: center;\"><a href=\"https://docs.google.com/forms/d/e/1FAIpQLSfei9WTHvDmOUHOjYWpI_QUxRAdACIeeKho2uSWOuVvhIuofw/viewform\" target=\"_blank\" rel=\"noopener\">Thoughts, suggestions, feedback</a></p>"
        },
        "id": "b17758212681948",
        "type": "text"
      },
      {
        "id": "b17760592402894",
        "type": "image",
        "content": {
          "url": "",
          "alt": "",
          "caption": ""
        }
      }
    ],
    "theme": {
      "_logo_had_base64": true,
      "accent_color": "#db800f",
      "bg_color": "#ffffff",
      "header_color": "#544b2b",
      "header_height": 100,
      "header_image": "",
      "logo_align": "left",
      "logo_height": 50,
      "logo_radius": 6,
      "logo_text": "\u25c8 Draftspace",
      "logo_url": "/static/nl_uploads/logo_b2540a15432741db819dd413e73875a6.png",
      "logo_width": 94
    },
    "created_at": "2026-04-10T06:18:55.324000",
    "updated_at": "2026-04-13T05:47:25.242000"
  }
]
def get_forms(uid=None):
    if _ok: return list(_db.forms.find({"user_id":uid} if uid else {}))
    return _FORMS
def get_responses(fid):
    if _ok: return list(_db.responses.find({"form_id":str(fid)}))
    return []
def get_newsletters(uid=None):
    if _ok: return list(_db.newsletters.find({"user_id":uid} if uid else {}))
    return _NL
def is_connected(): return _ok
