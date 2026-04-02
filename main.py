import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
from dotenv import load_dotenv
import google.generativeai as genai
from fpdf import FPDF

load_dotenv()

# ====================== CONFIG ======================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("Please set TELEGRAM_TOKEN and GEMINI_API_KEY in .env or Railway variables")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Simple in-memory storage (fine for starting)
user_states = {}

# ================== PDF GENERATOR ==================
class CVPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.set_text_color(0, 51, 102)  # Navy blue
        self.cell(0, 10, "Professional CV", ln=1, align="C")
        self.ln(5)

    def section_title(self, title):
        self.set_font("Arial", "B", 12)
        self.set_text_color(255, 140, 0)  # Gold
        self.cell(0, 8, title, ln=1)
        self.ln(2)

    def section_body(self, text):
        self.set_font("Arial", "", 10)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 5, text)
        self.ln(3)

# ================== BOT HANDLERS ==================
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "👋 Welcome to **Professional CV Hub Bot**!\n\n"
        "I will help you create a professional CV + Cover Letter.\n"
        "Type /cv to begin."
    )

@dp.message(Command("cv"))
async def start_cv(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = {"step": 1}
    await message.answer("Let's build your CV!\n\nPlease send your **full name**:")

@dp.message(F.text)
async def handle_steps(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    state = user_states[user_id]
    step = state.get("step")

    if step == 1:
        state["name"] = message.text
        state["step"] = 2
        await message.answer("Great! Now send your **phone number and email** (e.g. +251 9xx xxx xxx | email@example.com)")

    elif step == 2:
        state["contact"] = message.text
        state["step"] = 3
        await message.answer("Next: Send your **education** (University, Degree, Year)")

    elif step == 3:
        state["education"] = message.text
        state["step"] = 4
        await message.answer("Now send your **work experience** (Job title, Company, Dates, 3-4 bullet points)")

    elif step == 4:
        state["experience"] = message.text
        state["step"] = 5
        await message.answer("Send your **skills** (comma separated, e.g. Python, Networking, Flutter, Cisco)")

    elif step == 5:
        state["skills"] = message.text
        state["step"] = 6
        await message.answer("Finally, what is the **target job** or industry? (e.g. IT Instructor, NGO, Scholarship)")

    elif step == 6:
        state["target"] = message.text

        # Use Gemini to format everything professionally
        prompt = f"""
        You are an expert CV writer. Create a clean, professional CV using this information:
        Name: {state['name']}
        Contact: {state['contact']}
        Education: {state['education']}
        Experience: {state['experience']}
        Skills: {state['skills']}
        Target: {state['target']}

        Format it in modern style with strong action verbs and achievements focus.
        Return only the final formatted CV text (no extra comments).
        """

        response = model.generate_content(prompt)
        cv_text = response.text

        # Generate PDF
        pdf = CVPDF()
        pdf.add_page()
        pdf.section_title("Professional Summary")
        pdf.section_body("Experienced IT professional seeking opportunities in " + state['target'])
        pdf.section_title("Education")
        pdf.section_body(state['education'])
        pdf.section_title("Experience")
        pdf.section_body(state['experience'])
        pdf.section_title("Skills")
        pdf.section_body(state['skills'])

        filename = f"CV_{state['name'].replace(' ', '_')}.pdf"
        pdf.output(filename)

        # Send to user
        await message.answer("✅ Your professional CV is ready!")
        await message.answer_document(types.FSInputFile(filename), caption="Here is your CV!\n\nWant a Cover Letter too? Type /cover")

        # Clean up
        if os.path.exists(filename):
            os.remove(filename)
        del user_states[user_id]

# ================== RUN BOT ==================
async def main():
    print("🚀 Professional CV Hub Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
