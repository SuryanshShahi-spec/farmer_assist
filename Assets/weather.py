import tkinter as tk
from tkinter import messagebox
import requests
import os
from dotenv import load_dotenv

load_dotenv()

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
        
        # Configure Main Window
        self.root.title("EcoWeather (Weatherstack)")
        self.root.geometry("400x520")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)
        
        # Header Banner Area
        self.header_frame = tk.Frame(self.root, bg=PRIMARY_GREEN, height=70)
        self.header_frame.pack(fill="x")
        self.header_frame.pack_propagate(False)
        
        self.title_label = tk.Label(
            self.header_frame, 
            text="🌿 EcoWeather", 
            font=("Helvetica", 18, "bold"), 
            fg="#FFFFFF", 
            bg=PRIMARY_GREEN
        )
        self.title_label.pack(pady=18)
        
        # Search Entry Bar Widget
        self.search_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.search_frame.pack(pady=20, padx=20, fill="x")
        
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
        self.card.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Output Labels inside Card UI
        self.location_lbl = tk.Label(self.card, text="Search for a city", font=("Helvetica", 16, "bold"), fg=PRIMARY_GREEN, bg=CARD_COLOR)
        self.location_lbl.pack(pady=(25, 5))
        
        self.temp_lbl = tk.Label(self.card, text="--°C", font=("Helvetica", 42, "bold"), fg=TEXT_MAIN, bg=CARD_COLOR)
        self.temp_lbl.pack(pady=10)
        
        self.desc_lbl = tk.Label(self.card, text="Conditions will appear here", font=("Helvetica", 12, "italic"), fg=TEXT_MUTED, bg=CARD_COLOR)
        self.desc_lbl.pack(pady=5)
        
        # Divider Line Graphic Accent
        self.divider = tk.Frame(self.card, bg=BG_COLOR, height=1)
        self.divider.pack(fill="x", padx=30, pady=20)
        
        # Stats Breakdown Layout Grid 
        self.stats_frame = tk.Frame(self.card, bg=CARD_COLOR)
        self.stats_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        self.humidity_lbl = tk.Label(self.stats_frame, text="💧 Humidity: --", font=("Helvetica", 11), fg=TEXT_MAIN, bg=CARD_COLOR, anchor="w")
        self.humidity_lbl.pack(side="left", expand=True, fill="x")
        
        self.wind_lbl = tk.Label(self.stats_frame, text="💨 Wind: --", font=("Helvetica", 11), fg=TEXT_MAIN, bg=CARD_COLOR, anchor="e")
        self.wind_lbl.pack(side="right", expand=True, fill="x")

    def clear_placeholder(self, event):
        if self.city_entry.get() == "Enter city name...":
            self.city_entry.delete(0, tk.END)
            self.city_entry.config(fg=TEXT_MAIN)

    def restore_placeholder(self, event):
        if not self.city_entry.get().strip():
            self.city_entry.insert(0, "Enter city name...")
            self.city_entry.config(fg="#A0AFA5")

    def fetch_weather(self):
        city_name = self.city_entry.get().strip()
        if not city_name or city_name == "Enter city name...":
            messagebox.showwarning("Input Error", "Please enter a valid city name.")
            return

        # Weatherstack Base URL (Free accounts use 'http' explicitly)
        base_url = "http://api.weatherstack.com/current"
        query_params = {
            'access_key': self.access_key,
            'query': city_name,
            'units': 'm'  # 'm' sets metric values (Celsius, km/h)
        }
        
        try:
            response = requests.get(base_url, params=query_params)
            data = response.json()
            
            # Weatherstack signals successful extraction if the "success" flag is not explicitly False
            if "success" not in data or data["success"] != False:
                # API Target Data Extraction Strategy
                city = data['location']['name']
                country = data['location']['country']
                temp = data['current']['temperature']
                humidity = data['current']['humidity']
                wind_speed = data['current']['wind_speed']
                
                # 'weather_descriptions' is delivered as a string array list index entry
                descriptions = data['current']['weather_descriptions']
                desc = descriptions[0] if descriptions else "N/A"
                
                # Dynamic Layout UI State Refresh Engine
                self.location_lbl.config(text=f"{city}, {country}")
                self.temp_lbl.config(text=f"{temp}°C")
                self.desc_lbl.config(text=desc.capitalize())
                self.humidity_lbl.config(text=f"💧 Humidity: {humidity}%")
                self.wind_lbl.config(text=f"💨 Wind: {wind_speed} km/h")
                
            else:
                # Parse Weatherstack dedicated inner error descriptions
                error_info = data.get("error", {})
                error_msg = error_info.get("info", "Failed to get weather data.")
                messagebox.showerror("API Error", f"Error: {error_msg}")
                
        except requests.exceptions.RequestException:
            messagebox.showerror("Connection Error", "Could not connect to the Weatherstack data server.")


if __name__ == "__main__":
    access_key = os.getenv("WEATHERSTACK_API_KEY")
    if not access_key:
        raise RuntimeError(
            "WEATHERSTACK_API_KEY is missing. Add it to the project's .env file."
        )
    
    root_window = tk.Tk()
    app = WeatherApp(root_window, access_key)
    root_window.mainloop()
