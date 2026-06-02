def run_math_loop():
    print("--- Running External Logic ---")
    mock_volumes = [10.5, 22.1, 8.4]
    total_mass = 0.0
    density = 2400.0 
    
    for vol in mock_volumes:
        # ---> PUT YOUR RED DOT ON THIS EXACT LINE IN PYCHARM <---
        mass = vol * density 
        total_mass += mass
        print(f"Processed volume {vol} m3 -> {mass} kg")
        
    return total_mass