import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.api_client import APIClient

def get_verdict_color(verdict):
    """Return color based on verdict"""
    colors = {
        'High': '#28a745',
        'Medium': '#ffc107', 
        'Low': '#dc3545'
    }
    return colors.get(verdict, '#6c757d')

def display_evaluation_card(evaluation):
    """Display evaluation result in a card format"""
    verdict_color = get_verdict_color(evaluation.get('verdict', 'Unknown'))
    
    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**{evaluation.get('resume_name', 'Unknown Resume')}**")
            st.caption(f"Job: {evaluation.get('job_title', 'Unknown Position')}")
        
        with col2:
            st.metric("Score", f"{evaluation.get('relevance_score', 0):.1f}%")
        
        with col3:
            st.markdown(f"<span style='color: {verdict_color}; font-weight: bold;'>{evaluation.get('verdict', 'Unknown')}</span>", 
                       unsafe_allow_html=True)
        
        # Expandable details
        with st.expander("View Details"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🚫 Missing Elements")
                missing = evaluation.get('missing_elements', {})
                
                if missing.get('skills'):
                    st.write("**Skills:**")
                    for skill in missing['skills'][:5]:  # Show top 5
                        st.write(f"• {skill}")
                
                if missing.get('projects'):
                    st.write("**Projects:**")
                    for project in missing['projects'][:3]:  # Show top 3
                        st.write(f"• {project}")
                
                if missing.get('certifications'):
                    st.write("**Certifications:**")
                    for cert in missing['certifications'][:3]:  # Show top 3
                        st.write(f"• {cert}")
            
            with col2:
                st.subheader("💡 Improvement Feedback")
                feedback = evaluation.get('feedback', 'No feedback available.')
                st.markdown(f"""
                <div style='background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff;'>
                {feedback}
                </div>
                """, unsafe_allow_html=True)
            
            # Skill matching chart
            if evaluation.get('skill_matches'):
                st.subheader("📊 Skill Matching")
                skill_data = evaluation['skill_matches']
                
                fig = go.Figure(data=go.Bar(
                    x=list(skill_data.keys()),
                    y=list(skill_data.values()),
                    marker_color=['#28a745' if v > 70 else '#ffc107' if v > 40 else '#dc3545' for v in skill_data.values()]
                ))
                fig.update_layout(
                    title="Skill Match Percentage",
                    xaxis_title="Skills",
                    yaxis_title="Match %",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)

def results_page():
    st.title("📊 Evaluation Results")
    
    # Load evaluations
    try:
        evaluations_data = st.session_state.api_client.get_evaluations()
        if not evaluations_data or not evaluations_data.get('evaluations'):
            st.info("No evaluation results found. Please upload resumes and job descriptions first.")
            return
        
        evaluations = evaluations_data['evaluations']
    except Exception as e:
        st.error(f"Error loading evaluations: {str(e)}")
        return
    
    # Filters
    st.subheader("🔍 Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        job_roles = list(set([eval.get('job_title', 'Unknown') for eval in evaluations]))
        selected_role = st.selectbox("Job Role", ["All"] + job_roles)
    
    with col2:
        score_range = st.slider("Score Range", 0, 100, (0, 100))
    
    with col3:
        verdicts = list(set([eval.get('verdict', 'Unknown') for eval in evaluations]))
        selected_verdict = st.selectbox("Verdict", ["All"] + verdicts)
    
    # Apply filters
    filtered_evaluations = evaluations
    
    if selected_role != "All":
        filtered_evaluations = [e for e in filtered_evaluations if e.get('job_title') == selected_role]
    
    if selected_verdict != "All":
        filtered_evaluations = [e for e in filtered_evaluations if e.get('verdict') == selected_verdict]
    
    filtered_evaluations = [
        e for e in filtered_evaluations 
        if score_range[0] <= e.get('relevance_score', 0) <= score_range[1]
    ]
    
    st.markdown(f"**Showing {len(filtered_evaluations)} of {len(evaluations)} results**")
    
    # Summary statistics
    if filtered_evaluations:
        st.markdown("---")
        st.subheader("📈 Summary Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_score = sum(e.get('relevance_score', 0) for e in filtered_evaluations) / len(filtered_evaluations)
            st.metric("Average Score", f"{avg_score:.1f}%")
        
        with col2:
            high_verdicts = len([e for e in filtered_evaluations if e.get('verdict') == 'High'])
            st.metric("High Relevance", high_verdicts)
        
        with col3:
            medium_verdicts = len([e for e in filtered_evaluations if e.get('verdict') == 'Medium'])
            st.metric("Medium Relevance", medium_verdicts)
        
        with col4:
            low_verdicts = len([e for e in filtered_evaluations if e.get('verdict') == 'Low'])
            st.metric("Low Relevance", low_verdicts)
        
        # Score distribution chart
        st.subheader("📊 Score Distribution")
        scores = [e.get('relevance_score', 0) for e in filtered_evaluations]
        
        fig = px.histogram(
            x=scores,
            nbins=20,
            title="Distribution of Relevance Scores",
            labels={'x': 'Relevance Score (%)', 'y': 'Number of Resumes'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Verdict distribution pie chart
        col1, col2 = st.columns(2)
        
        with col1:
            verdict_counts = {}
            for eval in filtered_evaluations:
                verdict = eval.get('verdict', 'Unknown')
                verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
            
            if verdict_counts:
                fig = px.pie(
                    values=list(verdict_counts.values()),
                    names=list(verdict_counts.keys()),
                    title="Verdict Distribution",
                    color_discrete_map={
                        'High': '#28a745',
                        'Medium': '#ffc107',
                        'Low': '#dc3545'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Top missing skills
            all_missing_skills = []
            for eval in filtered_evaluations:
                missing = eval.get('missing_elements', {})
                if missing.get('skills'):
                    all_missing_skills.extend(missing['skills'][:3])
            
            if all_missing_skills:
                skill_counts = {}
                for skill in all_missing_skills:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1
                
                top_skills = dict(sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10])
                
                fig = px.bar(
                    x=list(top_skills.values()),
                    y=list(top_skills.keys()),
                    orientation='h',
                    title="Most Common Missing Skills",
                    labels={'x': 'Frequency', 'y': 'Skills'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    # Display results
    st.markdown("---")
    st.subheader("📋 Detailed Results")
    
    if not filtered_evaluations:
        st.info("No results match the current filters.")
        return
    
    # Sort options
    sort_by = st.selectbox(
        "Sort by:",
        ["Relevance Score (High to Low)", "Relevance Score (Low to High)", "Resume Name", "Job Title"]
    )
    
    if sort_by == "Relevance Score (High to Low)":
        filtered_evaluations.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    elif sort_by == "Relevance Score (Low to High)":
        filtered_evaluations.sort(key=lambda x: x.get('relevance_score', 0))
    elif sort_by == "Resume Name":
        filtered_evaluations.sort(key=lambda x: x.get('resume_name', ''))
    elif sort_by == "Job Title":
        filtered_evaluations.sort(key=lambda x: x.get('job_title', ''))
    
    # Display evaluation cards
    for i, evaluation in enumerate(filtered_evaluations):
        with st.container():
            display_evaluation_card(evaluation)
            if i < len(filtered_evaluations) - 1:
                st.markdown("---")
    
    # Export option
    st.markdown("---")
    if st.button("📥 Export Results to CSV"):
        df_data = []
        for eval in filtered_evaluations:
            df_data.append({
                'Resume Name': eval.get('resume_name', ''),
                'Job Title': eval.get('job_title', ''),
                'Relevance Score': eval.get('relevance_score', 0),
                'Verdict': eval.get('verdict', ''),
                'Missing Skills': ', '.join(eval.get('missing_elements', {}).get('skills', [])[:5]),
                'Feedback': eval.get('feedback', '')[:100] + '...' if len(eval.get('feedback', '')) > 100 else eval.get('feedback', '')
            })
        
        df = pd.DataFrame(df_data)
        csv = df.to_csv(index=False)
        
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="resume_evaluation_results.csv",
            mime="text/csv"
        )