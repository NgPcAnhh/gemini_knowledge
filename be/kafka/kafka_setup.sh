#!/bin/bash
# kafka_setup.sh - Tạo các Kafka topics cho hệ thống tín dụng cầm đồ
# Chạy bên trong container kafka: docker exec -it kafka bash < kafka_setup.sh

KAFKA_BIN="/usr/bin"
BOOTSTRAP="localhost:9092"

topics=(
  "customer.events"
  "asset.events"
  "loan.application.events"
  "loan.decision.events"
  "loan.disbursement.events"
  "loan.repayment.events"
  "loan.status.events"
  "cashflow.events"
  "risk.signal.events"
  "opex.events"
  "payroll.events"
  "depreciation.events"
  "alert.events"
)

echo "=== Tạo Kafka Topics ==="
for topic in "${topics[@]}"; do
  echo "Creating topic: $topic"
  kafka-topics --create \
    --bootstrap-server "$BOOTSTRAP" \
    --replication-factor 1 \
    --partitions 3 \
    --topic "$topic" \
    --if-not-exists
done

echo "=== Danh sách topics ==="
kafka-topics --list --bootstrap-server "$BOOTSTRAP"
echo "=== DONE ==="
