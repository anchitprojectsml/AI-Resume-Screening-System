import streamlit as st
import re
import pdfplumber
from sentence_transformers import SentenceTransformer, util
import pandas as pd


use_mapping = st.checkbox("Use Smart Skill Mapping", value=True)

skills_list = [

    'python', 'sql',
    
    # ML variants
    'machine learning', 'ml',
    'deep learning', 'dl',
    'nlp', 'natural language processing',
    'artificial intelligence', 'ai',
    
    'tensorflow', 'pytorch', 'scikit-learn', 'xgboost',
    
    'pandas', 'numpy', 'tableau', 'power bi',
    
    'aws', 'azure', 'gcp', 'docker', 'kubernetes',
    
    'java', 'react', 'spring boot'

]
skill_mapping = {
    'artificial intelligence': ['machine learning', 'nlp'],
    'machine learning': ['artificial intelligence'],
    'nlp': ['machine learning'],
}

def extract_skills(text):
    found = []
    text = text.lower()
    
    
    text = text.replace('/', ' ')
    text = text.replace('-', ' ')
    
    
    text = re.sub(r'\s+', ' ', text)
    
    
    text = text.replace('machinelearning', 'machine learning')
    text = text.replace('deeplearning', 'deep learning')
    
    
    text = text.replace('ml', 'machine learning')
    text = text.replace('ai', 'artificial intelligence')
    
    for skill in skills_list:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text):
            found.append(skill)
    
    return list(set(found))
    

def get_missing_skills(resume, job, use_mapping=True):
    
    resume_skills = extract_skills(resume)
    job_skills = extract_skills(job)

    if use_mapping:
        expanded_resume = set(resume_skills)

        for skill in resume_skills:
            if skill in skill_mapping:
                expanded_resume.update(skill_mapping[skill])
    else:
        expanded_resume = set(resume_skills)

    missing = list(set(job_skills) - expanded_resume)

    return missing

def extract_text_from_pdf(file):
    text = ""

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text+= page.extract_text() or ""
    
    return text.lower()
model = SentenceTransformer('all-MiniLM-L6-v2')

st.title("🤖 AI Resume Screening System (ATS)")
st.caption("Smart candidate ranking using NLP + BERT")

st.markdown("---")

job = st.text_area("Enter Job Description")
mode = st.radio("Choose Mode", ["Single Resume", "Multiple Resume Ranking"])
st.markdown("---")
if mode == "Single Resume":
    uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

elif mode == "Multiple Resume Ranking":
    uploaded_files = st.file_uploader("Upload Multiple Resumes (PDF)", type=["pdf"], accept_multiple_files=True)

def rank_resumes(files,job):
    results=[]
    for file in files:
        resume = extract_text_from_pdf(file)
        score = get_score(resume,job)

        results.append({
            "name": file.name,
            "score": score
        })
    return sorted(results,key=lambda x: x['score'],reverse=True)




def get_score(resume, job):
    emb1 = model.encode(resume, convert_to_tensor=True)
    emb2 = model.encode(job, convert_to_tensor=True)
    
    score = util.cos_sim(emb1, emb2)
    
    return round(float(score) * 100, 2)

st.markdown("---")

if st.button("Analyze"):

    if mode == "Single Resume":
        if uploaded_file and job:

            resume = extract_text_from_pdf(uploaded_file)

            score = get_score(resume, job)
            st.success(f"Match Score: {score}%")

            missing = get_missing_skills(resume, job, use_mapping)

            if missing:
                st.warning(f"Missing Skills: {', '.join(missing)}")
            else:
                st.success("No missing skills 🎉")

        else:
            st.warning("Please upload resume and enter job description")


    elif mode == "Multiple Resume Ranking":
        if uploaded_files and job:

            ranking = rank_resumes(uploaded_files, job)
            df = pd.DataFrame(ranking)
            df = df.sort_values(by='score',ascending=False)

            top_candidate = df.iloc[0]

            st.success(f"⭐ Top Candidate: {top_candidate['name']} ({top_candidate['score']}%)")
            st.subheader("📈 Score Visualization")
            st.bar_chart(df.set_index("name")["score"])

            st.subheader("📊 Candidate Ranking Table")
            st.dataframe(df)

            st.subheader("🏆 Top Candidates")

            for i, candidate in enumerate(ranking[:5]):
                st.write(f"{i+1}. {candidate['name']} - {candidate['score']}%")

        else:
            st.warning("Upload resumes and job description")
            st.subheader("Why Top Candidate?")

            top_resume_text = extract_text_from_pdf(uploaded_files[0])

            top_skills = extract_skills(top_resume_text)
            job_skills = extract_skills(job)

            matched = list(set(top_skills) & set(job_skills))

            st.write(f"Matched Skills: {', '.join(matched)}")
           

        
        csv = df.to_csv(index=False).encode('utf-8')

        st.download_button(
            label = "📥 Download Results as CSV",
            data = csv,
            file_name='resume_ranking.csv',
            mime='text/csv',



        )
