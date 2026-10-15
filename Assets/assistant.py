import tkinter as tk
from tkinter import messagebox
import requests
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# --- Theme Configuration Constants ---
BG_COLOR = "#F4F7F5"          # Soft off-white background
PRIMARY_GREEN = "#2A7B4C"     # Forest green for headers and primary actions
ACCENT_GREEN = "#3B945E"      # Lighter green for button hover effect
CARD_COLOR = "#FFFFFF"        # Pure white for content containers
TEXT_MAIN = "#1E2922"         # Deep charcoal green for high contrast readability
TEXT_MUTED = "#556B5D"        # Slate green for secondary labels


class WeatherApp:
    def __init__(self, root, access_key):
        self.root = root
        self.access_key = access_key
        self.deepseek_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("DEEPSEEK_API")
        
        # Configure Main Window
        self.root.title("AgriEco Weather & AI Assistant")
        self.root.geometry("450x700")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)
        
        # Header Banner Area
        self.header_frame = tk.Frame(self.root, bg=PRIMARY_GREEN, height=70)
        self.header_frame.pack(fill="x")
        self.header_frame.pack_propagate(False)
        
        self.title_label = tk.Label(
            self.header_frame, 
            text="🌿 AgriEco Weather Assistant", 
            font=("Helvetica", 16, "bold"), 
            fg="#FFFFFF", 
            bg=PRIMARY_GREEN
        )
        self.title_label.pack(pady=18)
        
        # Search Entry Bar Widget
        self.search_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.search_frame.pack(pady=15, padx=20, fill="x")
        
        self.city_entry = tk.Entry(
            self.search_frame, 
            font=("Helvetica", 13), 
            bg="#FFFFFF", 
            fg=TEXT_MAIN, 
            bd=0, 
            highlightthickness=1,
            highlightbackground="#D0D7D1",
            highlightcolor=PRIMARY_GREEN
        )
        self.city_entry.insert(0, "Enter city name...")
        self.city_entry.bind("<FocusIn>", self.clear_placeholder)
        self.city_entry.bind("<FocusOut>", self.restore_placeholder)
        self.city_entry.bind("<Return>", lambda event: self.fetch_weather())
        self.city_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 10))
        
        # Action Buttons
        self.search_btn = tk.Button(
            self.search_frame, 
            text="Search", 
            font=("Helvetica", 11, "bold"), 
            bg=PRIMARY_GREEN, 
            fg="#FFFFFF", 
            activebackground=ACCENT_GREEN,
            activeforeground="#FFFFFF",
            bd=0, 
            cursor="hand2", 
            command=self.fetch_weather
        )
        self.search_btn.pack(side="right", ipady=6, ipadx=15)
        self.search_btn.bind("<Enter>", lambda e: self.search_btn.config(bg=ACCENT_GREEN))
        self.search_btn.bind("<Leave>", lambda e: self.search_btn.config(bg=PRIMARY_GREEN))
        
        # Weather Results Display Card Panel
        self.card = tk.Frame(self.root, bg=CARD_COLOR, bd=0, highlightthickness=1, highlightbackground="#E2E8E4")
        self.card.pack(pady=5, padx=20, fill="x")
        
        self.location_lbl = tk.Label(self.card, text="Search for a city", font=("Helvetica", 14, "bold"), fg=PRIMARY_GREEN, bg=CARD_COLOR)
        self.location_lbl.pack(pady=(15, 2))
        
        self.temp_lbl = tk.Label(self.card, text="--°C", font=("Helvetica", 36, "bold"), fg=TEXT_MAIN, bg=CARD_COLOR)
        self.temp_lbl.pack(pady=2)
        
        self.desc_lbl = tk.Label(self.card, text="Conditions will appear here", font=("Helvetica", 11, "italic"), fg=TEXT_MUTED, bg=CARD_COLOR)
        self.desc_lbl.pack(pady=2)
        
        # Stats Breakdown Layout Grid 
        self.stats_frame = tk.Frame(self.card, bg=CARD_COLOR)
        self.stats_frame.pack(fill="x", padx=20, pady=(10, 15))
        
        self.humidity_lbl = tk.Label(self.stats_frame, text="💧 Humidity: --", font=("Helvetica", 10), fg=TEXT_MAIN, bg=CARD_COLOR, anchor="w")
        self.humidity_lbl.pack(side="left", expand=True, fill="x")
        
        self.wind_lbl = tk.Label(self.stats_frame, text="💨 Wind: --", font=("Helvetica", 10), fg=TEXT_MAIN, bg=CARD_COLOR, anchor="e")
        self.wind_lbl.pack(side="right", expand=True, fill="x")

        # --- AI FARMING ASSISTANT INTERFACE PANEL ---
        self.ai_frame = tk.LabelFrame(
            self.root, 
            text="🤖 AI Agricultural Advisor", 
            font=("Helvetica", 11, "bold"),
            fg=PRIMARY_GREEN,
            bg=CARD_COLOR, 
            bd=0, 
            highlightthickness=1, 
            highlightbackground="#E2E8E4"
        )
        self.ai_frame.pack(pady=15, padx=20, fill="both", expand=True)

        # Scrolled Text Box for AI feedback
        self.ai_text = tk.Text(
            self.ai_frame, 
            wrap="word", 
            font=("Helvetica", 10), 
            bg=CARD_COLOR, 
            fg=TEXT_MAIN,
            bd=0,
            padx=10,
            pady=10
        )
        self.ai_text.pack(fill="both", expand=True)
        self.ai_text.insert("1.0", "Search for a location's weather to receive automated AI farming recommendations based on current local metrics.")
        self.ai_text.config(state="disabled")

    def clear_placeholder(self, event):
        if self.city_entry.get() == "Enter city name...":
            self.city_entry.delete(0, tk.END)
            self.city_entry.config(fg=TEXT_MAIN)

    def restore_placeholder(self, event):
        if not self.city_entry.get().strip():
            self.city_entry.insert(0, "Enter city name...")
            self.city_entry.config(fg="#A0AFA5")

    def generate_farming_advice(self, city, temp, humidity, desc, wind):
        if not self.deepseek_key:
            self.update_ai_box("Error: Add DEEPSEEK_API or DEEPSEEK_API_KEY to the project's .env file.")
            return

        self.update_ai_box("Analyzing metrics & generating localized advisor briefing...")
        
        system_prompt = (
            "You are an expert agronomy and smart-farming AI assistant. "
            "Analyze the provided local current weather data metrics and generate a concise, "
            "highly actionable farming briefing. Provide specific bullet points for:\n"
            "- Irrigation needs based on temperature and humidity\n"
            "- Crop protection and pest warnings\n"
            "- Field-operation advice based on wind and rain\n"
            "Keep the response simple, brief, and tailored to these measurements."
        )
        user_message = (
            f"Location: {city}\n"
            f"Temperature: {temp}°C\n"
            f"Humidity: {humidity}%\n"
            f"Condition: {desc}\n"
            f"Wind speed: {wind} km/h"
        )

        try:
            response = requests.post(
                "https://api.deepseek.com/chat/completions",
                headers={"Authorization": f"Bearer {self.deepseek_key}"},
                json={
                    "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 700,
                },
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()["choices"][0]["message"]["content"].strip()
            self.update_ai_box(result)
        except requests.exceptions.Timeout:
            self.update_ai_box("DeepSeek request timed out. Please try again.")
        except requests.exceptions.HTTPError as error:
            status = error.response.status_code if error.response is not None else "unknown"
            self.update_ai_box(
                f"DeepSeek returned HTTP {status}. Check the API key and configured model."
            )
        except (requests.exceptions.RequestException, KeyError, IndexError, TypeError, ValueError):
            self.update_ai_box("Could not get a valid response from DeepSeek. Please try again.")

    def update_ai_box(self, message):
        self.ai_text.config(state="normal")
        self.ai_text.delete("1.0", tk.END)
        self.ai_text.insert("1.0", message)
        self.ai_text.config(state="disabled")

    def fetch_weather(self):
        city_name = self.city_entry.get().strip()
        if not city_name or city_name == "Enter city name...":
            messagebox.showwarning("Input Error", "Please enter a valid city name.")
            return

        base_url = "http://api.weatherstack.com/current"
        query_params = {
            'access_key': self.access_key,
            'query': city_name,
            'units': 'm'
        }
        
        try:
            response = requests.get(base_url, params=query_params)
            response.raise_for_status()
            data = response.json()
            
            if "success" not in data or data["success"] != False:
                city = data['location']['name']
                country = data['location']['country']
                temp = data['current']['temperature']
                humidity = data['current']['humidity']
                wind_speed = data['current']['wind_speed']
                descriptions = data['current']['weather_descriptions']
                desc = descriptions[0] if descriptions else "N/A"
                
                # Update Weather UI Elements
                self.location_lbl.config(text=f"{city}, {country}")
                self.temp_lbl.config(text=f"{temp}°C")
                self.desc_lbl.config(text=desc.capitalize())
                self.humidity_lbl.config(text=f"💧 Humidity: {humidity}%")
                self.wind_lbl.config(text=f"💨 Wind: {wind_speed} km/h")
                
                # Kick off LangChain background generation pass
                self.generate_farming_advice(city, temp, humidity, desc, wind_speed)
                
            else:
                error_info = data.get("error", {})
                error_msg = error_info.get("info", "Failed to get weather data.")
                messagebox.showerror("API Error", f"Error: {error_msg}")
        except requests.exceptions.RequestException as error:
            messagebox.showerror("Connection Error", f"Could not fetch weather data:\n{error}")


if __name__ == "__main__":
    access_key = os.getenv("WEATHERSTACK_API_KEY")
    if not access_key:
        raise RuntimeError(
            "WEATHERSTACK_API_KEY is missing. Add it to the project's .env file."
        )

    root_window = tk.Tk()
    app = WeatherApp(root_window, access_key)
    root_window.mainloop()
