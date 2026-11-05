from pptx import Presentation
from pptx.util import Inches, Pt

prs = Presentation()

def add_slide(title, bullets):
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = title
    tf = slide.placeholders[1].text_frame
    tf.text = bullets[0]
    for bullet in bullets[1:]:
        p = tf.add_paragraph()
        p.text = bullet
        p.font.size = Pt(20)

# Slide 1
title_slide_layout = prs.slide_layouts[0]
slide = prs.slides.add_slide(title_slide_layout)
slide.shapes.title.text = "Boréal Marché"
slide.placeholders[1].text = "Customer Intelligence Platform\nHossam Siyam\n420-977-VA Capstone Project"

# Slide 2
add_slide("Slide 1: The Problem", [
    "Retention: They give a 15% coupon to everyone, even loyal customers.",
    "Recommendations: The 'You might also like' section is old and hard-coded.",
    "Support: Two employees answer the same 40 questions every day."
])

# Slide 3
add_slide("Slide 2: The Solution (3 AI Brains)", [
    "Head A (Prediction): Will this customer buy again in 90 days?",
    "Head B (Recommendation): What should we suggest in their cart?",
    "Head C (Assistant): A chatbot that answers questions in English and French."
])

# Slide 4
add_slide("Slide 3: The Data & Leakage Fix", [
    "Started with 525,000 transactions, cleaned it to 400,000.",
    "Major Fix: Prevented Data Leakage. The AI only learns from the past to predict the future."
])

# Slide 5
add_slide("Slide 4: Head A - The Prediction Model", [
    "Tested 9 different AI models.",
    "The winner: Logistic Regression (Accurate and easy to explain).",
    "Accuracy Score: 0.78 (Very good for real-world retail)."
])

# Slide 6
add_slide("Slide 5: Head A - The Money Decision", [
    "Default threshold (0.5) made $72,000.",
    "We changed the threshold to 0.01.",
    "New Profit: $100,232.",
    "We saved Boréal Marché an extra $28,200 just by changing the math!"
])

# Slide 7
add_slide("Slide 6: Head B - The Recommendation Engine", [
    "Analyzed shopping baskets to find patterns (e.g., 'If you buy charcoal, you buy matches').",
    "Created 55 strong rules.",
    "Result: Our engine is 6.3 times better than just showing the most popular items."
])

# Slide 8
add_slide("Slide 7: Head C - The AI Assistant", [
    "Uses our real company policies to answer questions in English and French.",
    "Engineering Trade-off: Used TF-IDF instead of PyTorch to fit the 512MB server limit.",
    "Result: Scored 100% on our 40-question test."
])

# Slide 9
add_slide("Slide 8: Deployment (Render vs. AWS)", [
    "Live API: Hosted on Render to avoid billing.",
    "Training code is 100% compatible with AWS SageMaker.",
    "Live Frontend: Hosted on Streamlit Cloud.",
    "Code: Fully automated testing on GitHub (CI/CD)."
])

# Slide 10
add_slide("Slide 9: Monitoring Dashboard", [
    "Tracks requests, speed, and errors.",
    "Data Drift: Alerts us if customer behavior changes.",
    "Safe Retraining: Opens a Pull Request for human review."
])

# Slide 11
add_slide("Slide 10: Ethics & Law 25", [
    "Fairness Audit: Checked if AI is unfair to certain groups.",
    "Human Review: A human must review the list before sending coupons.",
    "Privacy: We follow Quebec's Law 25."
])

# Slide 12
add_slide("Slide 11: Conclusion", [
    "A fully working AI system.",
    "Live on the internet.",
    "Monitored and safe.",
    "Saves the company $28,200."
])

# Slide 13
add_slide("Slide 12: Thank You", [
    "Thank you for listening.",
    "Questions?",
    "Live App: boreal-marche-frontend.streamlit.app"
])

prs.save('reports/977_D6_Siyam_Slides.pptx')
print("✅ PowerPoint generated successfully at reports/977_D6_Siyam_Slides.pptx")