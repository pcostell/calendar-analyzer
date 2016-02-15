# Calendar Analyzer

## Overview
This is a simple application for analyzing your calendar.

For example, we can see how much time we spent in 2015 in events with meeting in the name like this:

    python analyze.py -s 2015-01-01 -e 2015-12-31 calendar.ics "/.*meeting.*/Meetings/i"

## Setup

In order to run, make sure to install the necessary dependencies with

    pip install -r requirements.txt