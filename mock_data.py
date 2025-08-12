import random
from datetime import datetime, timedelta
from faker import Faker
from models import Alert, AlertImportance, AssetClass, Underlier, Process, AlertStatus

fake = Faker()

# Mock data configuration
NUM_ALERTS = 50
USERS = [
    "analyst@company.com",
    "trader@company.com",
    "manager@company.com",
    "support@company.com",
    "operations@company.com"
]

UNDERLIERS = [
    Underlier(id="AAPL", name="Apple Inc.", asset_class=AssetClass.EQUITIES),
    Underlier(id="MSFT", name="Microsoft Corp.", asset_class=AssetClass.EQUITIES),
    Underlier(id="GOOGL", name="Alphabet Inc.", asset_class=AssetClass.EQUITIES),
    Underlier(id="UST10Y", name="10Y US Treasury", asset_class=AssetClass.FIXED_INCOME),
    Underlier(id="GC1", name="Gold Futures", asset_class=AssetClass.COMMODITIES),
    Underlier(id="CL1", name="Crude Oil Futures", asset_class=AssetClass.COMMODITIES),
    Underlier(id="EURUSD", name="EUR/USD", asset_class=AssetClass.FX),
    Underlier(id="BTC", name="Bitcoin", asset_class=AssetClass.CRYPTO),
    Underlier(id="ETH", name="Ethereum", asset_class=AssetClass.CRYPTO)
]

PROCESSES = [
    Process(id="pricing", name="Pricing Engine", description="Main pricing process"),
    Process(id="datafeed", name="Data Feed", description="Market data ingestion"),
    Process(id="risk", name="Risk Calculation", description="Portfolio risk analysis"),
    Process(id="settlement", name="Settlement", description="Trade settlement process"),
    Process(id="reporting", name="Reporting", description="Regulatory reporting"),
    Process(id="trading", name="Trading System", description="Order management system")
]

ALERT_TITLES = [
    "Price Discrepancy Detected",
    "Late Data Feed",
    "Volatility Spike",
    "Failed Trade",
    "Margin Threshold Breached",
    "System Latency Detected",
    "Reference Data Mismatch",
    "Position Limit Exceeded",
    "Authentication Failure",
    "Network Connectivity Issue",
    "Database Connection Error",
    "Calculation Timeout",
    "Missing Market Data",
    "Corporate Action Alert",
    "Settlement Failure"
]

def generate_alert_description(title):
    descriptions = {
        "Price Discrepancy Detected": f"Price difference of {random.uniform(0.1, 5.0):.2f}% detected between {fake.words(nb=2, unique=True)[0]} and {fake.words(nb=2, unique=True)[1]} systems",
        "Late Data Feed": f"Data feed delayed by {random.randint(5, 120)} seconds",
        "Volatility Spike": f"Volatility increased by {random.uniform(10, 200):.1f}% in last {random.randint(1, 60)} minutes",
        "Failed Trade": f"Trade {fake.uuid4()} failed with error: {fake.sentence()}",
        "Margin Threshold Breached": f"Margin utilization at {random.uniform(90, 120):.1f}% of limit",
        "System Latency Detected": f"Processing latency of {random.randint(100, 5000)}ms detected",
        "Reference Data Mismatch": f"Mismatch detected in {fake.word()} reference data between {fake.words(nb=2, unique=True)[0]} and {fake.words(nb=2, unique=True)[1]}",
        "Position Limit Exceeded": f"Position limit exceeded by {random.uniform(1, 15):.1f}% for {random.choice(['client', 'product', 'strategy'])}",
        "Authentication Failure": f"Failed login attempts from IP {fake.ipv4()}",
        "Network Connectivity Issue": f"Packet loss of {random.uniform(1, 25):.1f}% detected on {fake.word()} network",
        "Database Connection Error": f"Connection pool exhausted - {random.randint(5, 50)} pending requests",
        "Calculation Timeout": f"Calculation exceeded timeout of {random.randint(30, 300)} seconds",
        "Missing Market Data": f"Missing {fake.word()} data for {random.choice(['opening auction', 'closing prices', 'corporate actions'])}",
        "Corporate Action Alert": f"Corporate action detected for {fake.company()} - {fake.word()}",
        "Settlement Failure": f"Settlement failed for {random.randint(1, 20)} trades worth {random.randint(10000, 1000000)} {fake.currency_code()}"
    }
    return descriptions.get(title, fake.sentence())

def generate_alert_status(timestamp):
    now = datetime.utcnow()
    alert_age = (now - timestamp).total_seconds() / 3600  # hours
    
    if alert_age > 24:
        return AlertStatus.RESOLVED
    elif alert_age > 6:
        return random.choice([AlertStatus.IN_PROGRESS, AlertStatus.ASSIGNED, AlertStatus.RESOLVED])
    elif alert_age > 2:
        return random.choice([AlertStatus.ACKNOWLEDGED, AlertStatus.ASSIGNED])
    else:
        return AlertStatus.NEW

def generate_alert():
    timestamp = datetime.utcnow() - timedelta(hours=random.randint(0, 72))
    importance = random.choices(
        [AlertImportance.CRITICAL, AlertImportance.WARNING, AlertImportance.INFORMATION],
        weights=[0.2, 0.5, 0.3]
    )[0]
    title = random.choice(ALERT_TITLES)
    description = generate_alert_description(title)
    
    # Select 1-3 asset classes
    asset_classes = random.sample(list(AssetClass), k=random.randint(1, 3))
    
    # Select 1-3 underliers from the appropriate asset classes
    eligible_underliers = [u for u in UNDERLIERS if u.asset_class in asset_classes]
    underliers = random.sample(
        eligible_underliers, 
        k=min(random.randint(1, 3), len(eligible_underliers)))
    
    # Select 1-2 processes
    processes = random.sample(PROCESSES, k=random.randint(1, 2))
    
    status = generate_alert_status(timestamp)
    
    assigned_to = random.choice(USERS) if status in [AlertStatus.ASSIGNED, AlertStatus.IN_PROGRESS] else None
    acknowledged_by = random.choice(USERS) if status in [AlertStatus.ACKNOWLEDGED, AlertStatus.ASSIGNED, AlertStatus.IN_PROGRESS, AlertStatus.RESOLVED] else None
    acknowledged_at = (timestamp + timedelta(minutes=random.randint(5, 120))).isoformat() if acknowledged_by else None
    
    return Alert(
        id=fake.uuid4(),
        timestamp=timestamp.isoformat(),
        importance=importance,
        title=title,
        description=description,
        asset_classes=asset_classes,
        underliers=underliers,
        processes=processes,
        status=status,
        assigned_to=assigned_to,
        acknowledged_by=acknowledged_by,
        acknowledged_at=acknowledged_at,
        comments=fake.sentence() if random.random() > 0.7 else None
    )

def generate_mock_alerts(num_alerts=NUM_ALERTS):
    return [generate_alert() for _ in range(num_alerts)]

# Example usage:
if __name__ == "__main__":
    alerts = generate_mock_alerts(10)
    for alert in alerts:
        print(f"{alert.timestamp} [{alert.importance.value}] {alert.title}")
        print(f"  Status: {alert.status.value}")
        if alert.assigned_to:
            print(f"  Assigned to: {alert.assigned_to}")
        print(f"  Asset Classes: {[ac.value for ac in alert.asset_classes]}")
        print(f"  Underliers: {[u.name for u in alert.underliers]}")
        print(f"  Processes: {[p.name for p in alert.processes]}")
        print("-" * 80)