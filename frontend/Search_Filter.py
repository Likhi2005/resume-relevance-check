import streamlit as st
import pandas as pd
from utils.api_client import APIClient

def search_filter_page():
    st.title("🔍 Advanced Search & Filter")
    
    st.markdown("""
    Use advanced filters to find specific evaluation results and analyze patterns.
    """)
    
    # Load all evaluations
    try:
        evaluations_data = st.session_state.api_client.get_evaluations()
        if not evaluations_data or not evaluations_data.get('evaluations'):
            st.info("No evaluation results found. Please upload resumes and job descriptions first.")
            return
        
        evaluations = evaluations_data['evaluations']
    except Exception as e:
        st.error(f"Error loading evaluations: {str(e)}")
        return
    
    # Advanced Filters Section
    st.subheader("🎯 Advanced Filters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Basic Filters**")
        
        # Job role filter
        job_roles = list(set([eval.get('job_title', 'Unknown') for eval in evaluations]))
        selected_roles = st.multiselect("Job Roles", job_roles, default=job_roles)
        
        # Verdict filter
        verdicts = ['High', 'Medium', 'Low']
        selected_verdicts = st.multiselect("Verdict", verdicts, default=verdicts)
        
        # Score range
        min_score, max_score = st.slider(
            "Score Range",
            min_value=0,
            max_value=100,
            value=(0, 100),
            step=5
        )
    
    with col2:
        st.markdown("**Text Search**")
        
        # Resume name search
        resume_search = st.text_input("Search Resume Name", placeholder="Enter resume name...")
        
        # Skills search
        skills_search = st.text_input("Required Skills", placeholder="Enter skills (comma-separated)...")
        
        # Feedback search
        feedback_search = st.text_input("Search Feedback", placeholder="Search in feedback text...")
    
    # Apply filters
    filtered_evaluations = evaluations
    
    # Basic filters
    if selected_roles:
        filtered_evaluations = [e for e in filtered_evaluations if e.get('job_title') in selected_roles]
    
    if selected_verdicts:
        filtered_evaluations = [e for e in filtered_evaluations if e.get('verdict') in selected_verdicts]
    
    filtered_evaluations = [
        e for e in filtered_evaluations 
        if min_score <= e.get('relevance_score', 0) <= max_score
    ]
    
    # Text filters
    if resume_search:
        filtered_evaluations = [
            e for e in filtered_evaluations 
            if resume_search.lower() in e.get('resume_name', '').lower()
        ]
    
    if skills_search:
        search_skills = [skill.strip().lower() for skill in skills_search.split(',')]
        filtered_evaluations = [
            e for e in filtered_evaluations
            if any(
                any(skill in missing_skill.lower() for missing_skill in e.get('missing_elements', {}).get('skills', []))
                for skill in search_skills
            )
        ]
    
    if feedback_search:
        filtered_evaluations = [
            e for e in filtered_evaluations
            if feedback_search.lower() in e.get('feedback', '').lower()
        ]
    
    # Results summary
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Results", len(evaluations))
    with col2:
        st.metric("Filtered Results", len(filtered_evaluations))
    with col3:
        if len(evaluations) > 0:
            filter_percentage = (len(filtered_evaluations) / len(evaluations)) * 100
            st.metric("Filter Match", f"{filter_percentage:.1f}%")
    
    # Quick filter buttons
    st.markdown("**Quick Filters:**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🎯 High Performers (Score > 80)"):
            st.session_state.quick_filter = "high_performers"
    
    with col2:
        if st.button("⚠️ Needs Improvement (Score < 50)"):
            st.session_state.quick_filter = "needs_improvement"
    
    with col3:
        if st.button("🔧 Missing Skills"):
            st.session_state.quick_filter = "missing_skills"
    
    with col4:
        if st.button("🔄 Reset Filters"):
            st.session_state.quick_filter = "reset"
    
    # Apply quick filters
    if 'quick_filter' in st.session_state:
        if st.session_state.quick_filter == "high_performers":
            filtered_evaluations = [e for e in filtered_evaluations if e.get('relevance_score', 0) > 80]
        elif st.session_state.quick_filter == "needs_improvement":
            filtered_evaluations = [e for e in filtered_evaluations if e.get('relevance_score', 0) < 50]
        elif st.session_state.quick_filter == "missing_skills":
            filtered_evaluations = [
                e for e in filtered_evaluations 
                if e.get('missing_elements', {}).get('skills', [])
            ]
        elif st.session_state.quick_filter == "reset":
            # Reset would require reloading, or we can just clear the session state
            if 'quick_filter' in st.session_state:
                del st.session_state.quick_filter
    
    # Display results in table format
    if filtered_evaluations:
        st.markdown("---")
        st.subheader("📋 Search Results")
        
        # Create DataFrame for better display
        df_data = []
        for eval in filtered_evaluations:
            missing_skills = eval.get('missing_elements', {}).get('skills', [])
            df_data.append({
                'Resume': eval.get('resume_name', 'Unknown'),
                'Job Title': eval.get('job_title', 'Unknown'),
                'Score': f"{eval.get('relevance_score', 0):.1f}%",
                'Verdict': eval.get('verdict', 'Unknown'),
                'Missing Skills (Top 3)': ', '.join(missing_skills[:3]) if missing_skills else 'None',
                'Has Feedback': 'Yes' if eval.get('feedback') else 'No'
            })
        
        df = pd.DataFrame(df_data)
        
        # Display with sorting options
        sort_column = st.selectbox(
            "Sort by:",
            df.columns.tolist(),
            index=2  # Default to Score
        )
        
        ascending = st.checkbox("Ascending order", value=False)
        
        if sort_column == 'Score':
            # Special handling for score column
            df['Score_Numeric'] = df['Score'].str.replace('%', '').astype(float)
            df_sorted = df.sort_values('Score_Numeric', ascending=ascending).drop('Score_Numeric', axis=1)
        else:
            df_sorted = df.sort_values(sort_column, ascending=ascending)
        
        st.dataframe(df_sorted, use_container_width=True, height=400)
        
        # Detailed view option
        st.markdown("**View Details:**")
        selected_resume = st.selectbox(
            "Select resume for detailed view:",
            ["Select..."] + [eval.get('resume_name', f'Resume {i}') for i, eval in enumerate(filtered_evaluations)]
        )
        
        if selected_resume != "Select...":
            selected_eval = next(
                (eval for eval in filtered_evaluations if eval.get('resume_name') == selected_resume),
                None
            )
            
            if selected_eval:
                st.markdown("---")
                st.subheader(f"📄 Details for {selected_resume}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Relevance Score", f"{selected_eval.get('relevance_score', 0):.1f}%")
                    st.metric("Verdict", selected_eval.get('verdict', 'Unknown'))
                    st.write(f"**Job Title:** {selected_eval.get('job_title', 'Unknown')}")
                
                with col2:
                    missing = selected_eval.get('missing_elements', {})
                    
                    if missing.get('skills'):
                        st.write("**Missing Skills:**")
                        for skill in missing['skills'][:5]:
                            st.write(f"• {skill}")
                    
                    if missing.get('certifications'):
                        st.write("**Missing Certifications:**")
                        for cert in missing['certifications'][:3]:
                            st.write(f"• {cert}")
                
                # Feedback
                if selected_eval.get('feedback'):
                    st.subheader("💡 Personalized Feedback")
                    st.markdown(f"""
                    <div style='background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff;'>
                    {selected_eval['feedback']}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Export filtered results
        st.markdown("---")
        if st.button("📥 Export Filtered Results"):
            csv = df_sorted.to_csv(index=False)
            st.download_button(
                label="Download Filtered Results CSV",
                data=csv,
                file_name=f"filtered_results_{len(filtered_evaluations)}_items.csv",
                mime="text/csv"
            )
    
    else:
        st.info("No results match your current filters. Try adjusting the filter criteria.")
    
    # Analytics section
    if filtered_evaluations:
        st.markdown("---")
        st.subheader("📊 Quick Analytics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_score = sum(e.get('relevance_score', 0) for e in filtered_evaluations) / len(filtered_evaluations)
            st.metric("Average Score", f"{avg_score:.1f}%")
        
        with col2:
            most_common_job = max(
                set(e.get('job_title', 'Unknown') for e in filtered_evaluations),
                key=lambda x: len([e for e in filtered_evaluations if e.get('job_title') == x])
            )
            st.metric("Most Common Job", most_common_job)
        
        with col3:
            high_performers = len([e for e in filtered_evaluations if e.get('relevance_score', 0) > 75])
            st.metric("High Performers (>75%)", high_performers)