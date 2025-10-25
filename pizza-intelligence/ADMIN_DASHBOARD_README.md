# 🍕 Pizza Intelligence Admin Dashboard

Comprehensive admin interface for viewing analytics, insights, and managing pizza agent responses with advanced filtering and visualization capabilities.

## Features

### 📊 Web Dashboard (`admin_dashboard.py`)
- **Interactive Filtering**: Filter by rating, coupon tier, date range, and story length
- **Real-time Analytics**: Live charts and metrics
- **User Management**: Email analytics and user insights
- **Content Analysis**: Keyword extraction and quality metrics
- **Export Capabilities**: CSV and JSON export options
- **Responsive Design**: Works on desktop and mobile

### 💻 Command Line Tool (`admin_insights.py`)
- **Quick Insights**: Fast command-line analytics
- **Flexible Filtering**: Multiple filter options
- **Batch Analysis**: Process large datasets efficiently
- **Export Ready**: Easy integration with scripts

## Quick Start

### 1. Install Dependencies
```bash
pip install streamlit plotly pandas numpy
```

### 2. Launch Web Dashboard
```bash
# Easy launcher (installs dependencies automatically)
python run_admin_dashboard.py

# Or run directly
streamlit run admin_dashboard.py --server.port 8502
```

### 3. Use Command Line Tool
```bash
# Basic summary
python admin_insights.py

# Filter high-rated stories
python admin_insights.py --min-rating 8 --show-stories

# Show premium tier insights
python admin_insights.py --tier PREMIUM --insights

# Filter by length and rating
python admin_insights.py --min-rating 7 --min-length 200 --show-stories --limit 5
```

## Dashboard Features

### 🔍 Filtering Options
- **Rating Range**: Filter stories by minimum and maximum ratings (1-10)
- **Coupon Tiers**: Select specific tiers (BASIC, STANDARD, PREMIUM)
- **Date Range**: Filter by date range
- **Story Length**: Minimum character count filter

### 📈 Analytics Views

#### Overview Metrics
- Total requests and coupons issued
- Conversion rate percentage
- Average story rating
- User engagement statistics

#### Visual Charts
- **Rating Distribution**: Bar chart of story ratings
- **Coupon Tier Distribution**: Pie chart of tier breakdown
- **Daily Activity**: Timeline of story submissions
- **Hourly Activity**: Peak usage hours

#### User Analytics
- **Email Domain Analysis**: Distribution of user email domains
- **User Tier Performance**: Coupon tiers for email users
- **User Rating Patterns**: Rating distribution for email users

#### Content Analysis
- **Keyword Extraction**: Most common words in stories
- **Quality Metrics**: High vs low quality story analysis
- **Length vs Rating Correlation**: Story length impact on ratings

### 📚 Story Management
- **Detailed View**: Expandable story cards with full details
- **Sorting Options**: Sort by timestamp, rating, length, or tier
- **Bulk Operations**: Filter and export multiple stories
- **Search Capabilities**: Find specific stories quickly

### 📤 Export Features
- **Filtered CSV Export**: Export current filtered dataset
- **Analytics Summary**: JSON export of key metrics
- **Email List Export**: User email data for marketing
- **Custom Reports**: Generate specific analytics reports

## Command Line Usage

### Basic Commands
```bash
# Show summary statistics
python admin_insights.py

# Show detailed insights
python admin_insights.py --insights

# View stories with filters
python admin_insights.py --show-stories --limit 5
```

### Advanced Filtering
```bash
# High-rated premium stories
python admin_insights.py --min-rating 8 --tier PREMIUM --show-stories

# Long, well-rated stories
python admin_insights.py --min-rating 7 --min-length 300 --insights

# Recent low-rated feedback
python admin_insights.py --max-rating 3 --show-stories
```

### Available Filters
- `--min-rating N`: Minimum rating (1-10)
- `--max-rating N`: Maximum rating (1-10)
- `--tier TIER`: Filter by tier (BASIC/STANDARD/PREMIUM)
- `--min-length N`: Minimum story length in characters
- `--show-stories`: Display individual stories
- `--limit N`: Limit number of stories shown
- `--insights`: Show detailed analysis

## Data Structure

The system analyzes the following data points:

### Story Data
```json
{
  "story": "User's pizza story text",
  "rating": 8,
  "tier": "PREMIUM",
  "timestamp": "2025-10-25T13:53:34.820854",
  "user_hash": "c71a9a78",
  "story_length": 375
}
```

### Analytics Metrics
- Total requests and conversions
- Rating distributions and averages
- Coupon tier performance
- Temporal usage patterns
- User engagement metrics

### User Analytics
- Email collection and domains
- User retention patterns
- Tier preference analysis
- Geographic insights (if available)

## Insights Generated

### Quality Analysis
- **High Quality Stories**: Rating 8-10 analysis
- **Engagement Patterns**: Length vs rating correlation
- **Content Themes**: Common keywords and topics
- **User Satisfaction**: Rating distribution insights

### Business Metrics
- **Conversion Rates**: Request to coupon conversion
- **Tier Performance**: Which tiers are most popular
- **Usage Patterns**: Peak hours and days
- **User Retention**: Repeat user analysis

### Content Insights
- **Story Themes**: What topics get high ratings
- **Length Optimization**: Ideal story length for engagement
- **Keyword Analysis**: Most effective content themes
- **Sentiment Patterns**: Positive vs negative feedback

## Customization

### Adding New Filters
Edit `admin_dashboard.py` to add custom filters:
```python
# Add new filter in sidebar
new_filter = st.sidebar.selectbox("New Filter", options)

# Apply filter to dataframe
filtered_df = filtered_df[filtered_df['column'] == new_filter]
```

### Custom Charts
Add new visualizations:
```python
# Create custom chart
fig = px.scatter(data, x='column1', y='column2')
st.plotly_chart(fig, use_container_width=True)
```

### Export Formats
Add new export options:
```python
# Custom export function
def export_custom_format(data):
    # Process data
    return formatted_data
```

## Troubleshooting

### Common Issues

1. **No Data Found**
   - Ensure the agent has been run and collected data
   - Check `pizza_agent_analytics.json` exists

2. **Import Errors**
   - Install missing packages: `pip install streamlit plotly pandas numpy`
   - Use the launcher script for automatic installation

3. **Port Conflicts**
   - Change port in launcher: `--server.port 8503`
   - Check for other Streamlit instances

4. **Performance Issues**
   - Use filters to reduce dataset size
   - Consider pagination for large datasets

### Data Validation
```bash
# Check data file exists and is valid
python -c "import json; print(json.load(open('pizza_agent_analytics.json')))"

# Validate story structure
python admin_insights.py --insights
```

## Integration

### With Existing Systems
- **API Integration**: Export data via REST endpoints
- **Database Sync**: Import/export to databases
- **Reporting Tools**: CSV export for external analysis
- **Email Marketing**: User email list export

### Automation
- **Scheduled Reports**: Cron job integration
- **Alert Systems**: Threshold-based notifications
- **Data Pipeline**: Automated data processing
- **Backup Systems**: Regular data exports

## Security Considerations

- **Data Privacy**: User hashes instead of identifiable info
- **Access Control**: Implement authentication if needed
- **Data Retention**: Configure data cleanup policies
- **Export Security**: Secure handling of exported data

## Future Enhancements

- Real-time data streaming
- Advanced ML insights
- Predictive analytics
- A/B testing framework
- Multi-language support
- Mobile app integration