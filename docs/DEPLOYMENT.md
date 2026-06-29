# Cognify v3.0 Deployment Guide

This document describes how to build, configure, and run the Cognify platform in production.

---

## 1. Prerequisites
- Docker (v20.10 or higher)
- Docker Compose (v2.0 or higher)

---

## 2. Environment Configuration
Copy the environment variables template and modify configurations:
```bash
cp .env.example .env
```
Ensure `COGNIFY_SECRET_KEY` is set to a secure, randomly generated string. Set `COGNIFY_BYPASS_AUTH` to `false` in production.

---

## 3. Running with Docker Compose
Start the application and its volume mounts in detached mode:
```bash
docker-compose up --build -d
```
Verify the server status:
```bash
docker-compose ps
docker-compose logs -f
```
The application will be accessible at `http://localhost:10000`.

---

## 4. Backups and Restores
Backups are performed using the online backup REST endpoints.
Trigger database backup:
```bash
curl -X POST http://localhost:10000/api/v1/admin/backup \
  -H "Authorization: Bearer <superadmin_token>" \
  -H "Content-Type: application/json" \
  -d '{"filename": "production_backup.db"}'
```
This produces the database copy along with its metadata sidecar (including Git commit, schema versions, and MD5 verification checksum).
