def get_farming_recommendations(
    prediction,
    temperature=None,
    humidity=None,
    rain_probability=None,
):
    label = prediction.lower().replace(" ", "_")
    tips = []

    if rain_probability is None:
        tips.append("Check the local rain forecast before irrigation or spraying.")
    elif rain_probability >= 70:
        tips.append("Rain likely; check forecast before irrigation.")
    else:
        tips.append("Check soil moisture before irrigation.")

    if temperature is not None and temperature >= 35:
        tips.append("High temperature; monitor soil moisture and plant stress.")

    if humidity is not None and humidity >= 85:
        tips.append("High humidity; inspect leaves for disease symptoms.")

    if "healthy" in label:
        tips.append("Model classified the leaf as healthy; keep monitoring.")
    elif "early_blight" in label:
        tips.append("Possible early blight; verify symptoms.")
    elif "late_blight" in label:
        tips.append("Possible late blight; seek agricultural guidance.")
    elif "septoria" in label:
        tips.append("Possible Septoria leaf spot; verify symptoms.")
    elif "bacterial_spot" in label:
        tips.append("Possible bacterial spot; verify before treatment.")
    else:
        tips.append("Verify the leaf condition with an agricultural expert.")

    return tips
