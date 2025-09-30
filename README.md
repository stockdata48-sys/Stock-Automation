# 📊 Stock Data Automation System

## What Does This Do?

This project automatically updates stock information in Salesforce with just one button click. It takes stock data from a Google Drive spreadsheet and uploads it directly into your Salesforce database - no manual copying and pasting needed!

---

## 🎯 How It Works (Simple Version)

```
Google Drive Spreadsheet → Button Click in Salesforce → Data Automatically Updates
```

**The Magic Behind It:**
1. Your team updates stock prices in a Google Drive Excel file
2. Someone clicks a button in Salesforce
3. The system reads the Excel file, processes the data, and uploads everything to Salesforce
4. Done! All your stock records are updated automatically

---

## 🔧 What's Included

### Main Files

- **`final_automation.py`** - The brain of the operation. This file:
  - Downloads the Excel file from Google Drive
  - Reads stock names, prices, and changes
  - Cleans up the data (removes messy formatting)
  - Uploads everything to Salesforce
  - Creates a backup CSV file (just in case!)

- **`app.py`** - The web service that connects your Salesforce button to the automation
  - Listens for button clicks from Salesforce
  - Runs the automation when triggered
  - Sends back a success or error message

- **`requirements.txt`** - A shopping list of all the software tools needed to run this project

- **`stockdata_mapping.sdl`** - The instruction manual that tells Salesforce how to match Excel columns to database fields

---

## 📋 What Information Gets Updated

For each stock, the system updates:
- **Stock Name** (like "AAOI-SD" or "TSLA-SD")
- **Previous Close Price** (the last closing price)
- **Change** (how much the price went up or down)

---

## 🚀 Setup Guide

### Step 1: Deploy to Render
1. Upload your code to GitHub
2. Go to [Render.com](https://render.com) and create a new Web Service
3. Connect it to your GitHub repository
4. Render will automatically detect it's a Python project

### Step 2: Add Your Secret Keys to Render
In Render's dashboard, add these environment variables (think of them as locked passwords):

- **`SF_USERNAME`** = Your Salesforce username (like john@company.com)
- **`SF_PASSWORD_TOKEN`** = Your Salesforce password + security token combined

**Where to find your Salesforce Security Token:**
- Log into Salesforce
- Click your profile picture → Settings
- Search for "Reset My Security Token"
- Check your email for the token
- Combine: `YourPassword` + `SecurityToken` (no spaces!)

### Step 3: Connect Salesforce to Your Automation

1. **Get Your Render API Link**
   - After deploying, Render gives you a URL like: `https://your-app-name.onrender.com`
   - Your full API endpoint will be: `https://your-app-name.onrender.com/run-job?api_key=150697`

2. **Create a Button in Salesforce**
   - Go to your Stock Data object in Salesforce
   - Create a new Button (Setup → Object Manager → Stock_Data__c → Buttons, Links, and Actions)
   - Button Type: "Detail Page Button"
   - Behavior: "Execute JavaScript"
   - In the button code, add:
   ```javascript
   window.open('https://your-app-name.onrender.com/run-job?api_key=150697');
   ```

3. **Add the Button to Your Page**
   - Edit the page layout for Stock Data
   - Drag your new button onto the page
   - Save and you're done!

---

## 🎬 How to Use It

1. **Update the Excel file** on Google Drive with new stock prices
2. **Go to any Stock Data record** in Salesforce
3. **Click the automation button** you created
4. **Wait 10-30 seconds** - the system will:
   - Download the latest Excel file
   - Process all the data
   - Update Salesforce records
   - Create a backup file
5. **Refresh the page** to see your updated data!

---

## 🔒 Security Features

- **API Key Protection**: Only requests with the correct API key (`150697`) can trigger the automation
- **Environment Variables**: Your Salesforce password never appears in the code - it's stored securely in Render
- **Automatic Backups**: Every time the automation runs, it saves a CSV backup with a timestamp

---

## 📊 Google Drive File Format

Your Excel file should have a sheet named **"Nightly-Template-Template"** with these columns:

| Stock Name | Previous Close | Change |
|------------|----------------|--------|
| AAOI-SD | 45.23 | 1.15 |
| TSLA-SD | 248.50 | -3.20 |

**The system automatically:**
- Finds these columns even if they have slightly different names
- Cleans up company names
- Handles missing or invalid data
- Converts everything to the right format for Salesforce

---

## ⚠️ Troubleshooting

### Button doesn't work?
- Check that Render is still running (free tier sleeps after inactivity)
- Verify the API URL in your button is correct
- Make sure the API key is `150697`

### Data not updating?
- Confirm the Excel file has the right sheet name
- Check that column names include "Stock Name", "Previous Close", and "Change"
- Look at Render logs to see error messages

### "Unauthorized" error?
- Double-check your `SF_USERNAME` and `SF_PASSWORD_TOKEN` in Render
- Make sure there are no extra spaces in the environment variables
- Verify your security token is current (Salesforce resets it if you change your password)

---

## 🎓 Technical Details (For Developers)

- **Framework**: FastAPI (lightweight, modern Python web framework)
- **Salesforce Integration**: simple-salesforce library with bulk upsert
- **Data Processing**: pandas for Excel reading and data manipulation
- **Deployment**: Render with automatic deploys from GitHub
- **Authentication**: Query parameter API key + Salesforce OAuth

---

## 📞 Support

If you run into issues:
1. Check the Render logs for error messages
2. Verify your Excel file format matches the expected structure
3. Confirm all environment variables are set correctly in Render
4. Test the API directly by visiting the URL in your browser

---

## 📝 Notes

- The system processes up to 200 records per batch for optimal performance
- Backup CSV files are saved with timestamps like `stockdata_backup_20250930_143022.csv`
- The Google Drive file ID is currently hardcoded as `1WuTVktuDnJh3UECy4EzeaAlH4Bm6pAY7`
- To use a different file, modify the `file_id` parameter in the API call

---

**Made to automate tedious data entry and save your time!**
