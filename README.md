# SaaS Subscription & Billing Platform

![CI Pipeline](https://github.com/hrithikkaran/saas-billing-platform/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Django](https://img.shields.io/badge/Django-DRF-success)
![Docker](https://img.shields.io/badge/docker-enabled-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Redis](https://img.shields.io/badge/Redis-enabled-red)
![Stripe](https://img.shields.io/badge/Stripe-Payments-635BFF)
![License](https://img.shields.io/badge/license-MIT-green)

A production-inspired **SaaS Subscription & Billing Platform** built with **Django REST Framework**. This project demonstrates modern backend engineering practices including authentication, multi-tenant organization management, subscription billing with Stripe, asynchronous task processing using Celery, containerization with Docker, CI automation using GitHub Actions, and code quality enforcement.

---

# Project Overview

This project simulates the backend of a modern SaaS application where organizations can register, manage members, subscribe to different plans, and handle recurring billing through Stripe.

The project is designed to showcase backend architecture, clean code practices, API development, asynchronous processing, testing, and DevOps fundamentals commonly used in real-world software development.

---

# Key Features

- JWT Authentication & Authorization
- Role-Based Access Control (RBAC)
- Multi-Tenant Organization Management
- Organization Invitation System
- Subscription & Billing Management
- Stripe Customer Integration
- Stripe Checkout Integration
- Stripe Billing Portal
- Stripe Webhook Handling
- Automatic Subscription Synchronization
- Payment Event Tracking
- Background Task Processing with Celery
- Redis Message Broker
- Health Check API
- Swagger / OpenAPI Documentation
- Docker & Docker Compose Support
- GitHub Actions Continuous Integration
- Code Quality with Ruff, Black & isort
- Pre-commit Hooks
- Unit & Integration Testing
- Structured Logging

---

# Tech Stack

### Backend

- Python 3.12
- Django
- Django REST Framework
- Simple JWT

### Database

- PostgreSQL

### Background Processing

- Celery
- Redis

### Payment Integration

- Stripe API
- Stripe Checkout
- Stripe Billing Portal
- Stripe Webhooks

### API Documentation

- Swagger / drf-spectacular

### Containerization

- Docker
- Docker Compose
- Gunicorn

### Testing

- Pytest
- Factory Boy
- Mocking

### Code Quality

- Ruff
- Black
- isort
- pre-commit

### CI/CD

- GitHub Actions

### Version Control

- Git
- GitHub

---

# Major Modules

- Authentication
- Organizations
- Membership Management
- Invitation Management
- Subscription Management
- Billing
- Payment Processing
- Notifications
- Health Monitoring

---

# Payment Features

This project integrates **Stripe** to simulate a real SaaS billing system.

Implemented payment features include:

- Stripe Customer Creation
- Checkout Session
- Subscription Management
- Plan Upgrade/Downgrade
- Subscription Cancellation
- Billing Portal
- Webhook Processing
- Payment Event Tracking

---

# Engineering Practices

This project follows modern backend development practices:

- Layered Architecture
- Service Layer Pattern
- Selector Layer Pattern
- RESTful API Design
- Environment-based Configuration
- Dockerized Development
- Continuous Integration
- Structured Logging
- Automated Code Formatting
- Linting & Static Analysis
- Background Task Processing
- Health Check Endpoint
- Test-Driven Development Practices

---

# Code Quality Tools

| Tool | Purpose |
|------|---------|
| Ruff | Linting |
| Black | Code Formatting |
| isort | Import Sorting |
| pre-commit | Git Hooks |
| GitHub Actions | Continuous Integration |

---

# Project Status

**Current Status:** Active Development

Completed modules include:

- Authentication
- Organization Management
- RBAC
- Invitation System
- Subscription & Billing
- Stripe Integration
- Celery & Redis
- Docker Support
- GitHub Actions CI
- Code Quality Tooling
- Testing

Future enhancements may include:

- AWS Deployment
- Monitoring & Alerting
- Admin Dashboard
- Usage-based Billing
- Multi-currency Support

---

# Project Owner

**Hrithik Karan**

GitHub: https://github.com/hrithikkaran

---

# License

This project is licensed under the **MIT License**.

Feel free to use this project for learning, experimentation, and personal development.
