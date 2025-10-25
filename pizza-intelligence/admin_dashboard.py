#!/usr/bin/env python3
"""
Pizza Intelligence Admin Dashboard
Comprehensive web interface for viewing analytics, insights, and managing responses
"""

import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from collections import Counter
import numpy as np
from config import ANALYTICS_FILE
from utils import PizzaAgentAnalytics

# Page config
st.set_page_config(
    page_title="Pizza Intelligence Admin Dashboard",
    page_icon="🍕",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_analytics_data():
    """Load and process analytics data"""
    try:
        with open(ANALYTICS_FILE, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        st.error("No analytics data found. Run the agent first to collect data.")
        return None
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def create_stories_dataframe(data):
    """Convert stories data to DataFrame for easier filtering"""
    if 'stories' not in data or not data['stories']:
        return pd.DataFrame()
    
    stories_df = pd.DataFrame(data['stories'])
    stories_df['timestamp'] = pd.to_datetime(stories_df['timestamp'])
    stories_df['date'] = stories_df['timestamp'].dt.date
    stories_df['hour'] = stories_df['timestamp'].dt.hour
    stories_df['word_count'] = stories_df['story'].str.split().str.len()
    
    return stories_df

def main():
    st.title("🍕 Pizza Intelligence Admin Dashboard")
    st.markdown("---")
    
    # Load data
    data = load_analytics_data()
    if not data:
        return
    
    # Create DataFrame
    stories_df = create_stories_dataframe(data)
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Rating filter
    if not stories_df.empty:
        min_rating = st.sidebar.slider(
            "Minimum Rating", 
            min_value=1, 
            max_value=10, 
            value=1,
            help="Filter stories by minimum rating"
        )
        
        max_rating = st.sidebar.slider(
            "Maximum Rating", 
            min_value=1, 
            max_value=10, 
            value=10,
            help="Filter stories by maximum rating"
        )
        
        # Tier filter
        available_tiers = stories_df['tier'].unique() if 'tier' in stories_df.columns else []
        selected_tiers = st.sidebar.multiselect(
            "Coupon Tiers",
            options=available_tiers,
            default=available_tiers,
            help="Filter by coupon tier"
        )
        
        # Date range filter
        if not stories_df.empty:
            min_date = stories_df['date'].min()
            max_date = stories_df['date'].max()
            
            date_range = st.sidebar.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                help="Filter by date range"
            )
        
        # Story length filter
        min_length = st.sidebar.number_input(
            "Minimum Story Length (characters)",
            min_value=0,
            value=0,
            help="Filter by minimum story length"
        )
        
        # Apply filters
        filtered_df = stories_df[
            (stories_df['rating'] >= min_rating) &
            (stories_df['rating'] <= max_rating) &
            (stories_df['tier'].isin(selected_tiers)) &
            (stories_df['story_length'] >= min_length)
        ]
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = filtered_df[
                (filtered_df['date'] >= start_date) &
                (filtered_df['date'] <= end_date)
            ]
    else:
        filtered_df = pd.DataFrame()
    
    # Main dashboard
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Requests", data.get('total_requests', 0))
    
    with col2:
        st.metric("Total Coupons", data.get('total_coupons_issued', 0))
    
    with col3:
        conversion_rate = (data.get('total_coupons_issued', 0) / max(data.get('total_requests', 1), 1)) * 100
        st.metric("Conversion Rate", f"{conversion_rate:.1f}%")
    
    with col4:
        avg_rating = np.mean(data.get('story_ratings', [0])) if data.get('story_ratings') else 0
        st.metric("Avg Rating", f"{avg_rating:.1f}/10")
    
    st.markdown("---")
    
    # Charts section
    if not filtered_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Rating Distribution")
            rating_counts = filtered_df['rating'].value_counts().sort_index()
            fig_rating = px.bar(
                x=rating_counts.index,
                y=rating_counts.values,
                labels={'x': 'Rating', 'y': 'Count'},
                title="Story Ratings Distribution"
            )
            fig_rating.update_layout(showlegend=False)
            st.plotly_chart(fig_rating, use_container_width=True)
        
        with col2:
            st.subheader("🎫 Coupon Tiers")
            tier_counts = filtered_df['tier'].value_counts()
            fig_tier = px.pie(
                values=tier_counts.values,
                names=tier_counts.index,
                title="Coupon Tier Distribution"
            )
            st.plotly_chart(fig_tier, use_container_width=True)
        
        # Time-based analytics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📅 Daily Activity")
            daily_counts = filtered_df.groupby('date').size()
            fig_daily = px.line(
                x=daily_counts.index,
                y=daily_counts.values,
                labels={'x': 'Date', 'y': 'Stories'},
                title="Stories per Day"
            )
            st.plotly_chart(fig_daily, use_container_width=True)
        
        with col2:
            st.subheader("🕐 Hourly Activity")
            hourly_counts = filtered_df.groupby('hour').size()
            fig_hourly = px.bar(
                x=hourly_counts.index,
                y=hourly_counts.values,
                labels={'x': 'Hour', 'y': 'Stories'},
                title="Stories by Hour of Day"
            )
            st.plotly_chart(fig_hourly, use_container_width=True)
    
    # Insights section
    st.markdown("---")
    st.header("💡 Insights & Analytics")
    
    if not filtered_df.empty:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("📝 Story Length Analysis")
            avg_length = filtered_df['story_length'].mean()
            median_length = filtered_df['story_length'].median()
            st.write(f"**Average Length:** {avg_length:.0f} characters")
            st.write(f"**Median Length:** {median_length:.0f} characters")
            
            # Length vs Rating correlation
            correlation = filtered_df['story_length'].corr(filtered_df['rating'])
            st.write(f"**Length-Rating Correlation:** {correlation:.3f}")
            
        with col2:
            st.subheader("⭐ Rating Insights")
            high_rated = len(filtered_df[filtered_df['rating'] >= 8])
            low_rated = len(filtered_df[filtered_df['rating'] <= 3])
            st.write(f"**High Rated (8-10):** {high_rated} stories")
            st.write(f"**Low Rated (1-3):** {low_rated} stories")
            
            # Most common rating
            most_common_rating = filtered_df['rating'].mode().iloc[0] if not filtered_df['rating'].mode().empty else "N/A"
            st.write(f"**Most Common Rating:** {most_common_rating}")
        
        with col3:
            st.subheader("🎯 Tier Performance")
            tier_avg_rating = filtered_df.groupby('tier')['rating'].mean()
            st.write("**Average Rating by Tier:**")
            for tier, avg in tier_avg_rating.items():
                st.write(f"- {tier}: {avg:.1f}")
    
    # Detailed stories view
    st.markdown("---")
    st.header("📚 Detailed Stories")
    
    if not filtered_df.empty:
        # Sort options
        sort_by = st.selectbox(
            "Sort by:",
            options=['timestamp', 'rating', 'story_length', 'tier'],
            index=0
        )
        
        sort_order = st.radio(
            "Order:",
            options=['Descending', 'Ascending'],
            horizontal=True
        )
        
        ascending = sort_order == 'Ascending'
        sorted_df = filtered_df.sort_values(by=sort_by, ascending=ascending)
        
        # Display stories
        st.write(f"Showing {len(sorted_df)} stories (filtered from {len(stories_df)} total)")
        
        for idx, row in sorted_df.iterrows():
            with st.expander(f"Story #{idx} - Rating: {row['rating']}/10 - Tier: {row['tier']} - {row['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                st.write("**Story:**")
                st.write(row['story'])
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(f"**Rating:** {row['rating']}/10")
                with col2:
                    st.write(f"**Tier:** {row['tier']}")
                with col3:
                    st.write(f"**Length:** {row['story_length']} chars")
                with col4:
                    st.write(f"**Words:** {row['word_count']}")
    else:
        st.info("No stories match the current filters.")
    
    # User Analytics section
    if 'user_emails' in data and data['user_emails']:
        st.markdown("---")
        st.header("👥 User Analytics")
        
        email_data = data['user_emails']
        email_df = pd.DataFrame([
            {
                'user_hash': user_hash,
                'email': info.get('email', ''),
                'domain': info.get('domain', ''),
                'coupon_tier': info.get('coupon_tier', ''),
                'story_rating': info.get('story_rating', ''),
                'timestamp': pd.to_datetime(info.get('timestamp', ''))
            }
            for user_hash, info in email_data.items()
        ])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("📧 Email Domains")
            domain_counts = email_df['domain'].value_counts()
            fig_domains = px.pie(
                values=domain_counts.values,
                names=domain_counts.index,
                title="Email Domain Distribution"
            )
            st.plotly_chart(fig_domains, use_container_width=True)
        
        with col2:
            st.subheader("🎫 Email User Tiers")
            email_tier_counts = email_df['coupon_tier'].value_counts()
            fig_email_tiers = px.bar(
                x=email_tier_counts.index,
                y=email_tier_counts.values,
                title="Coupon Tiers for Email Users"
            )
            st.plotly_chart(fig_email_tiers, use_container_width=True)
        
        with col3:
            st.subheader("⭐ Email User Ratings")
            email_ratings = email_df['story_rating'].value_counts().sort_index()
            fig_email_ratings = px.bar(
                x=email_ratings.index,
                y=email_ratings.values,
                title="Ratings from Email Users"
            )
            st.plotly_chart(fig_email_ratings, use_container_width=True)
        
        # Email users table
        st.subheader("📋 Email Users Details")
        st.dataframe(
            email_df[['email', 'domain', 'coupon_tier', 'story_rating', 'timestamp']],
            use_container_width=True
        )
    
    # Suggestions and Feedback Analysis
    st.markdown("---")
    st.header("💭 Content Analysis")
    
    if not filtered_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔍 Story Keywords")
            # Extract common words from stories
            all_text = ' '.join(filtered_df['story'].str.lower())
            words = all_text.split()
            # Filter out common words
            stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'was', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}
            filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
            word_counts = Counter(filtered_words)
            
            top_words = word_counts.most_common(10)
            if top_words:
                words_df = pd.DataFrame(top_words, columns=['Word', 'Count'])
                fig_words = px.bar(
                    words_df,
                    x='Count',
                    y='Word',
                    orientation='h',
                    title="Most Common Words in Stories"
                )
                st.plotly_chart(fig_words, use_container_width=True)
        
        with col2:
            st.subheader("📈 Quality Metrics")
            
            # High quality stories (rating >= 8)
            high_quality = filtered_df[filtered_df['rating'] >= 8]
            st.write(f"**High Quality Stories:** {len(high_quality)} ({len(high_quality)/len(filtered_df)*100:.1f}%)")
            
            # Average length by rating
            length_by_rating = filtered_df.groupby('rating')['story_length'].mean()
            fig_length_rating = px.scatter(
                x=length_by_rating.index,
                y=length_by_rating.values,
                title="Average Story Length by Rating",
                labels={'x': 'Rating', 'y': 'Average Length'}
            )
            st.plotly_chart(fig_length_rating, use_container_width=True)
    
    # Export section
    st.markdown("---")
    st.header("📤 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Export Filtered Data as CSV"):
            if not filtered_df.empty:
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"pizza_stories_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data to export")
    
    with col2:
        if st.button("📋 Export Analytics Summary"):
            summary = {
                'total_stories': len(filtered_df),
                'average_rating': filtered_df['rating'].mean() if not filtered_df.empty else 0,
                'tier_distribution': filtered_df['tier'].value_counts().to_dict() if not filtered_df.empty else {},
                'rating_distribution': filtered_df['rating'].value_counts().to_dict() if not filtered_df.empty else {},
                'export_timestamp': datetime.now().isoformat()
            }
            
            summary_json = json.dumps(summary, indent=2)
            st.download_button(
                label="Download Summary JSON",
                data=summary_json,
                file_name=f"pizza_analytics_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

if __name__ == "__main__":
    main()