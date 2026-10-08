# Multi-stage build for Go bot with SQLite (CGO)
FROM golang:1.22-alpine AS builder

# Install build dependencies for CGO (gcc, musl-dev)
RUN apk add --no-cache gcc musl-dev

WORKDIR /app

# Download dependencies
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build binary with CGO enabled
RUN CGO_ENABLED=1 GOOS=linux go build \
    -trimpath \
    -ldflags="-w -s" \
    -o /app/bin/bot_app .

# Final minimal runtime container
FROM alpine:3.20

# Install runtime dependencies: ca-certificates for Telegram API (HTTPS) and tzdata for timezones
RUN apk add --no-cache ca-certificates tzdata

# Create dedicated non-root user for security
RUN adduser -D -u 10001 -g "" appuser

WORKDIR /app

# Create directory for persistent SQLite database and set ownership
RUN mkdir -p /data && chown -R appuser:appuser /data

# Copy compiled binary from builder
COPY --from=builder /app/bin/bot_app /app/bot_app

USER appuser

# Default database location inside container
ENV SQLITE_PATH=/data/storage.db

ENTRYPOINT ["/app/bot_app"]
