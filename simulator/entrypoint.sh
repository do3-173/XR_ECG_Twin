#!/bin/bash
set -e

# Build command with environment variables
python smartwatch_simulator.py \
  --broker "${MQTT_BROKER:-mqtt}" \
  --port "${MQTT_PORT:-1883}" \
  --loop \
  --participant "${PARTICIPANT:-1}" \
  --session "${SESSION:-1}" \
  --max-videos "${MAX_VIDEOS:-1}" \
  ${RANDOM_PARTICIPANTS:+--random}
