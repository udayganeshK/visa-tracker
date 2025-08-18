# Visa Tracker

A subscription-based visa appointment tracking system that monitors visa availability and sends alerts to users.

## Features

- Track multiple visa types (B1/B2, B2 Dropbox)
- Email subscription management
- Configurable alert thresholds
- Location-based filtering
- Real-time availability monitoring

## Subscription Data

The system manages user subscriptions with the following structure:

- **Email**: User's email address for notifications
- **Visa Types**: Types of visas to monitor (B1/B2, B2 Dropbox)
- **Alert Threshold**: Days in advance to send alerts
- **Locations**: Specific embassy locations to monitor
- **Timestamps**: Creation and update tracking

## Usage

1. Users subscribe with their email and preferences
2. System monitors visa appointment availability
3. Alerts sent when appointments become available within threshold
4. Users can update their subscription preferences

## Setup

```bash
# Make scripts executable
chmod +x check_github.sh push_to_github.sh

# Check GitHub setup
./check_github.sh

# Push to GitHub
./push_to_github.sh
```

## Data Structure

Current subscriptions are stored in `subscriptions.json` with user preferences and monitoring settings.
