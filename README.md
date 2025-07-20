# 🎉 NameDayInstagramBot  

## 🧠 What the Project Does  

**NameDayInstagramBot** is an automated bot that performs the following tasks daily:  

- 📅 Checks who celebrates their name day in the Czech Republic  
- 🌍 Looks up any international and national holidays  
- 🎨 Generates a visually appealing image for each name day and holiday  
- 🤖 Creates a funny and friendly caption using AI  
- 📲 Posts the content on Instagram (including carousel posts)  
- 🌌 Adds NASA's Astronomy Picture of the Day as a bonus  

Each day, a fresh and engaging Instagram post is created without any human intervention.  

---  

## 🔁 How the Project Works  

1. 🗓️ Retrieves current name days, national holidays, and international observances  
2. 🔎 Searches for additional info for each name—number of bearers, origin, age, etc.  
3. 🖼️ Generates images: AI background or color gradient + text and statistics  
4. ✍️ Composes a caption using a language model (DeepSeek)  
5. 📤 Uploads everything to Instagram (images + text)  
6. 🧹 Cleans up old images that are no longer needed  

---  

## 📁 Project Structure  

| File | Description |  
|-------|-------|  
| `main.py` | Main orchestrator - handles data retrieval, image generation, AI captions, and Instagram publishing |  
| `name_info.py` | Fetches name days and detailed name information from Czech calendar sites |  
| `instagram_bot.py` | Manages Instagram authentication, duplicate checks, and post uploads |  
| `image_generator.py` | Creates AI-generated backgrounds/gradients and composes final images |  
| `api_handler.py` | Interfaces with external APIs (AI models, NASA APOD, Wikipedia) |  

### 🧩 Additional Components  

- `fonts/` - Montserrat fonts for image generation  
- `.env` - Configuration file for credentials and API keys  
- `output/` - Temporary storage for generated images  

---  

## 💡 Key Features  

- **Automated Publishing**: Fully hands-off daily Instagram posts  
- **AI Integration**: Uses language models for creative captions  
- **Data Enrichment**: Combines name statistics with holiday information  
- **Visual Appeal**: Generates professional-looking social media content  
- **NASA Integration**: Includes astronomy images for added engagement  

---

## 📸 Output samples

<img width="808" height="910" alt="image" src="https://github.com/user-attachments/assets/55ed6859-335e-43fc-8a9e-8287bf13b82e" />

<img width="1296" height="898" alt="image" src="https://github.com/user-attachments/assets/f2adda0e-6b88-452c-8909-afbe545b1f18" />

---

## 💬 Summary  

This bot combines:  
- 📚 Name day and holiday data  
- 🧠 AI-powered text generation  
- 🎨 Automated graphic design  
- 🌐 Social media automation  

To deliver unique daily content that celebrates name days in style! 🥳  
