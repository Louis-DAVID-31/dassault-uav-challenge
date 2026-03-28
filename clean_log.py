import os

def clean_uav_log(input_file):
    # Generate output filename (e.g., flight_log_clean.txt)
    base, ext = os.path.splitext(input_file)
    output_file = f"{base}_CLEANED{ext}"
    
    # These are the events we want to keep. 
    # We keep SPOTTED and VERIFIED to see the progression of a real hit.
    valid_events = ["VERIFIED", "SPOTTED"]
    
    cleaned_lines = []
    
    print(f"Opening {input_file} for cleaning...")
    
    try:
        with open(input_file, 'r') as f:
            for line in f:
                # 1. Always keep headers, footers, and the CSV column labels
                if line.startswith("=") or "TIME, FRAME, ID" in line or "Date:" in line or "Camera" in line:
                    cleaned_lines.append(line)
                    continue
                
                # 2. Check if the line contains a valid event
                # We split by comma to check the EVENT column (index 3)
                parts = line.split(',')
                if len(parts) > 3:
                    event_type = parts[3].strip()
                    if event_type in valid_events:
                        cleaned_lines.append(line)
                
                # 3. Keep summary data at the end
                if any(x in line for x in ["End Time:", "Total Frames:", "Average FPS:", "Successfully"]):
                    cleaned_lines.append(line)

        # Write the filtered data to the new file
        with open(output_file, 'w') as f:
            f.writelines(cleaned_lines)
            
        print(f"Success! Cleaned log saved to: {output_file}")
        print(f"Original size: {os.path.getsize(input_file)} bytes")
        print(f"Cleaned size:  {os.path.getsize(output_file)} bytes")

    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.")

# --- EXECUTION ---
# Replace this with your actual log filename
filename = input("File name: ")
filename = "logs/"+filename

if os.path.exists(filename):
    clean_uav_log(filename)
else:
    print(f"File: '{filename}' does not exist.")