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
    raise ValueError("Please set TELEGRAM_TOKEN and GEMINI_API_KEY in Railway Variables")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

user_states = {}

# ================== IMPROVED PDF CLASS ==================
class ProfessionalCVPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 18)
        self.set_text_color(0, 51, 102)   # Navy Blue
        self.cell(0, 12, "Professional CV", ln=1, align="C")
        self.set_font("Arial", "I", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "Prepared by Professional CV Hub", ln=1, align="C")
        self.ln(10)

    def section_title(self, title):
        self.set_font("Arial", "B", 13)
        self.set_text_color(255, 140, 0)  # Gold
        self.cell(0, 10, title.upper(), ln=1)
        self.set_draw_color(255, 140, 0)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def section_body(self, text):
        self.set_font("Arial", "", 10.5)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 6, text)
        self.ln(7)

    def add_contact(self, contact):
        self.set_font("Arial", "", 10.5)
        self.set_text_color(0, 51, 102)
        self.cell(0, 6, f"Contact: {contact}", ln=1, align="C")
        self.ln(8)

# ================== BOT HANDLERS ==================
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "👋 Welcome to **Professional CV Hub Bot**!\n\n"
        "I create clean, modern, and professional CVs.\n"
        "Type /cv to start building yours."
    )

@dp.message(Command("cv"))
async def start_cv(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = {"step": 1}
    await message.answer("Let's create your professional CV!\n\nPlease send your **full name**:")

@dp.message(F.text)
async def handle_steps(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    state = user_states[user_id]
    step = state.get("step")

    if step == 1:
        state["name"] = message.text.strip()
        state["step"] = 2
        await message.answer("✅ Got it!\nNow send your **phone number and email** (e.g. +251 933 615101 | haileyesusshibru19@gmail.com)")

    elif step == 2:
        state["contact"] = message.text.strip()
        state["step"] = 3
        await message.answer("Next: Send your **education** details\n(University, Degree, Graduation Year, GPA if good)")

    elif step == 3:
        state["education"] = message.text.strip()
        state["step"] = 4
        await message.answer("Now send your **work experience**\n(Include Job Title, Company, Dates, and 3-5 bullet points)")

    elif step == 4:
        state["experience"] = message.text.strip()
        state["step"] = 5
        await message.answer("Send your **key skills** (comma separated)")

    elif step == 5:
        state["skills"] = message.text.strip()
        state["step"] = 6
        await message.answer("Finally, what is the **target job / industry**?\n(e.g. IT Instructor, Network Admin, NGO IT Support)")

    elif step == 6:
        state["target"] = message.text.strip()

        # Use Gemini to format professionally
        prompt = f"""
        You are an expert CV writer for Ethiopian and international job markets in 2026.
        Create a clean, modern, ATS-friendly CV using this information:

        Name: {state['name']}
        Contact: {state['contact']}
        Education: {state['education']}
        Experience: {state['experience']}
        Skills: {state['skills']}
        Target: {state['target']}

        Use strong action verbs and keep it concise.
        Return ONLY the well-formatted CV text with clear section headings. No extra comments.
        """

        response = model.generate_content(prompt)
        formatted_cv = response.text

        # Generate PDF
        pdf = ProfessionalCVPDF()
        pdf.add_page()
        pdf.add_contact(state["contact"])

        pdf.section_title("Professional Summary")
        pdf.section_body(f"Results-driven IT professional with strong expertise in networking, teaching, and systems support. Seeking opportunities in {state['target']}.")

        pdf.section_title("Education")
        pdf.section_body(state["education"])

        pdf.section_title("Professional Experience")
        pdf.section_body(state["experience"])

        pdf.section_title("Technical Skills")
        pdf.section_body(state["skills"])

        filename = f"CV_{state['name'].replace(' ', '_')}.pdf"
        pdf.output(filename)

        # Send to user
        await message.answer("🎉 Your professional CV is ready!")
        await message.answer_document(
            types.FSInputFile(filename),
            caption=f"Here is your modern CV, {state['name'].split()[0]}!\n\n"
                    "Want a matching Cover Letter? Type /cover\n"
                    "Need human review? Contact @haileeyesus19"
        )

        # Cleanup
        if os.path.exists(filename):
            os.remove(filename)
        del user_states[user_id]

# ================== RUN BOT ==================
async def main():
    print("🚀 Professional CV Hub Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
