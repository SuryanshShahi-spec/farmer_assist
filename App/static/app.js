const pageTitles = {
  weather: "Weather overview",
  assistant: "FarmCast assistant",
  plants: "Plant analysis",
};

const pages = document.querySelectorAll(".page");
const navItems = document.querySelectorAll(".nav-item");
const toast = document.getElementById("toast");
let latestWeather = null;
let toastTimer;

function notify(message, isError = false) {
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 4300);
}

function activatePage(name) {
  pages.forEach((page) => page.classList.toggle("active", page.id === `page-${name}`));
  navItems.forEach((item) => item.classList.toggle("active", item.dataset.page === name));
  document.getElementById("page-title").textContent = pageTitles[name];
}

navItems.forEach((item) => item.addEventListener("click", () => activatePage(item.dataset.page)));
document.querySelectorAll("[data-open]").forEach((item) =>
  item.addEventListener("click", () => activatePage(item.dataset.open)),
);

const dateLabel = document.getElementById("date-label");
dateLabel.textContent = new Intl.DateTimeFormat(undefined, {
  weekday: "long",
  month: "long",
  day: "numeric",
}).format(new Date()).toUpperCase();

function weatherNote(weather) {
  const notes = [];
  if (Number(weather.temperature) >= 35) notes.push("Heat is high; check soil moisture and crop stress.");
  if (Number(weather.humidity) >= 85) notes.push("High humidity; scout leaves for fungal symptoms.");
  if (Number(weather.wind_speed_kmh) >= 25) notes.push("Wind is brisk; postpone spraying until conditions settle.");
  if (Number(weather.precipitation_mm) > 0) notes.push("Rain is being reported; check field drainage.");
  return notes[0] || "Check soil moisture before irrigation and keep scouting your crop.";
}

document.getElementById("weather-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.currentTarget.querySelector("button");
  const location = document.getElementById("location-input").value.trim();
  if (!location) return notify("Enter a location to search.", true);
  button.disabled = true;
  button.textContent = "Loading…";
  try {
    const response = await fetch("/api/weather", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ location }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Weather lookup failed.");
    latestWeather = data;
    document.getElementById("weather-location").textContent = data.location;
    document.getElementById("temperature").textContent = data.temperature ?? "--";
    document.getElementById("condition").textContent = data.condition || "Conditions unavailable";
    document.getElementById("feels-like").textContent = data.feels_like ?? "--";
    document.getElementById("humidity").textContent = data.humidity ?? "--";
    document.getElementById("wind-speed").textContent = data.wind_speed_kmh ?? "--";
    document.getElementById("wind-direction").textContent = data.wind_direction
      ? `From ${data.wind_direction}`
      : "Current wind";
    document.getElementById("precipitation").textContent = data.precipitation_mm ?? "--";
    document.getElementById("weather-time").textContent = data.observation_time
      ? `· ${data.observation_time}`
      : "";
    document.getElementById("field-note").textContent = weatherNote(data);
    document.getElementById("weather-advice").textContent = weatherNote(data);
    notify(`Weather updated for ${data.location}.`);
  } catch (error) {
    notify(error.message, true);
  } finally {
    button.disabled = false;
    button.innerHTML = "Search <span>→</span>";
  }
});

function addMessage(text, role) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role === "user" ? "user-message" : "assistant-message"}`;
  if (role === "assistant") {
    const avatar = document.createElement("span");
    avatar.className = "message-avatar";
    avatar.textContent = "✳";
    wrapper.append(avatar);
  }
  const content = document.createElement("div");
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  const label = document.createElement("small");
  label.textContent = role === "user" ? "You" : "FarmCast assistant";
  content.append(paragraph, label);
  wrapper.append(content);
  document.getElementById("chat-messages").append(wrapper);
  wrapper.scrollIntoView({ behavior: "smooth", block: "end" });
  return wrapper;
}

document.getElementById("chat-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = document.getElementById("chat-input");
  const button = event.currentTarget.querySelector("button");
  const question = input.value.trim();
  if (!question) return;
  addMessage(question, "user");
  input.value = "";
  button.disabled = true;
  const pending = addMessage("Thinking through your question…", "assistant");
  try {
    const response = await fetch("/api/assistant", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        location: latestWeather?.location || document.getElementById("location-input").value.trim(),
        weather_context: latestWeather
          ? `${latestWeather.temperature}°C, ${latestWeather.condition}, humidity ${latestWeather.humidity}%, wind ${latestWeather.wind_speed_kmh} km/h`
          : null,
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "The assistant could not respond.");
    pending.querySelector("p").textContent = data.answer;
  } catch (error) {
    pending.querySelector("p").textContent = error.message;
    notify(error.message, true);
  } finally {
    button.disabled = false;
  }
});

const imageInput = document.getElementById("plant-image");
const dropZone = document.getElementById("drop-zone");
const preview = document.getElementById("image-preview");

function showImage(file) {
  if (!file) return;
  if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
    imageInput.value = "";
    return notify("Choose a JPG, PNG, or WEBP image.", true);
  }
  if (file.size > 8 * 1024 * 1024) {
    imageInput.value = "";
    return notify("Image must be 8 MB or smaller.", true);
  }
  preview.src = URL.createObjectURL(file);
  preview.hidden = false;
  document.getElementById("upload-title").textContent = file.name;
  document.getElementById("upload-subtitle").textContent = "Click to choose a different photo";
}

imageInput.addEventListener("change", () => showImage(imageInput.files[0]));
["dragenter", "dragover"].forEach((name) =>
  dropZone.addEventListener(name, (event) => {
    event.preventDefault();
    dropZone.classList.add("dragover");
  }),
);
["dragleave", "drop"].forEach((name) =>
  dropZone.addEventListener(name, (event) => {
    event.preventDefault();
    dropZone.classList.remove("dragover");
  }),
);
dropZone.addEventListener("drop", (event) => {
  const [file] = event.dataTransfer.files;
  if (file) {
    const transfer = new DataTransfer();
    transfer.items.add(file);
    imageInput.files = transfer.files;
    showImage(file);
  }
});

function reportSection(title, value) {
  if (!Array.isArray(value) || !value.length) return "";
  return `<section class="report-section"><h4>${title}</h4><ul>${value
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("")}</ul></section>`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character],
  );
}

document.getElementById("plant-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const image = imageInput.files[0];
  const crop = document.getElementById("crop-name").value.trim();
  if (!image || !crop) return notify("Choose a leaf photo and enter a crop name.", true);
  const button = event.currentTarget.querySelector("button");
  const original = button.innerHTML;
  button.disabled = true;
  button.innerHTML = "Analyzing image…";
  const form = new FormData();
  form.append("image", image);
  form.append("crop", crop);
  form.append("growth_stage", document.getElementById("growth-stage").value);
  form.append("location", document.getElementById("plant-location").value.trim() || "Jalgaon, Maharashtra");
  if (latestWeather?.temperature != null) form.append("temperature", latestWeather.temperature);
  if (latestWeather?.humidity != null) form.append("humidity", latestWeather.humidity);
  try {
    const response = await fetch("/api/plants/analyze", { method: "POST", body: form });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Plant analysis failed.");
    const result = data.analysis;
    const score = Number(result.confidence_score);
    const card = document.getElementById("analysis-card");
    card.innerHTML = `<div class="report">
      <div class="report-head"><span class="report-status">✳</span><div><span class="eyebrow">VISUAL ASSESSMENT</span><h3>${escapeHtml(data.crop)} · ${escapeHtml(data.growth_stage)}</h3></div>${Number.isFinite(score) ? `<span class="report-confidence">${Math.round(score)}% confidence</span>` : ""}</div>
      <section class="report-section"><h4>Finding</h4><p>${escapeHtml(result.finding || "No clear finding could be determined.")}</p></section>
      ${reportSection("Visible symptoms", result.visible_symptoms)}
      ${reportSection("Possible concerns", result.possible_concerns)}
      ${reportSection("Recommended next steps", result.recommended_next_steps)}
      ${result.expert_advisory ? `<div class="report-warning">${escapeHtml(result.expert_advisory)}</div>` : ""}
    </div>`;
    notify("Plant report is ready.");
  } catch (error) {
    notify(error.message, true);
  } finally {
    button.disabled = false;
    button.innerHTML = original;
  }
});

fetch("/api/health")
  .then((response) => {
    if (!response.ok) throw new Error("API unavailable");
  })
  .catch(() => {
    document.querySelector(".api-status").innerHTML =
      '<span class="status-dot" style="background:#d78365"></span> API connection unavailable';
  });
