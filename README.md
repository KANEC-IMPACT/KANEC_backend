=======
# Kanec API

A FastAPI-based donation platform that enables cryptocurrency donations using Hedera HBAR tokens. The platform allows organizations to create donation projects, users to make donations, and provides transparent transaction tracking through Hedera's distributed ledger.

## Features

- **User Management**: Role-based authentication (Donor, Admin, Organization) with email verification and OTP
- **Project Management**: Create and manage donation projects with HBAR targets, image uploads, and verification workflow
- **HBAR Donations**: Secure cryptocurrency donations via Hedera network with real-time balance validation
- **P2P Transfers**: Direct HBAR transfers between user wallets with memo support and wallet validation
- **Wallet Integration**: Automatic Hedera wallet creation for users and projects with encrypted ECDSA private key storage
- **Transaction Tracing**: Verify and track donation transactions on Hedera Mirror Node with multiple format support
- **Organization Support**: Organization accounts for managing multiple projects with verification status
- **Advanced AI Analytics**: ML-powered donation insights, personalized project recommendations, and comprehensive platform analytics
- **Profile Management**: Complete user profile management with password changes, account deletion, and wallet export
- **Email Services**: SMTP email sending with Brevo/SendGrid integration for notifications and OTP verification
- **PostgreSQL Database**: Robust data storage with SQLAlchemy async ORM and Alembic migrations
- **Docker Support**: Containerized deployment with Docker Compose for development and production environments
- **Celery Integration**: Asynchronous task processing with Redis backend for background jobs
- **Rate Limiting**: API rate limiting with Redis for security and abuse prevention
- **Security**: Cryptography-based private key encryption and JWT authentication

## Technology Stack

- **Backend**: FastAPI (Python 3.12) with async/await support
- **Database**: PostgreSQL with SQLAlchemy async ORM
- **Blockchain**: Hedera SDK (hiero-sdk-python) for HBAR transactions and wallet management
- **Migration**: Alembic for database schema management
- **Authentication**: JWT tokens with role-based access control (Donor/Admin/Org)
- **Data Analysis**: Pandas, NumPy, Scikit-learn for ML-powered analytics
- **Task Queue**: Celery with Redis backend for asynchronous processing
- **Email**: Brevo/SendGrid API integration with FastAPI-Mail
- **Caching**: Redis for session management, rate limiting, and caching
- **Security**: Cryptography library for ECDSA private key encryption
- **Containerization**: Docker & Docker Compose for development/production
- **Testing**: Pytest with async support and comprehensive test coverage
- **Code Quality**: Black, isort, flake8, pylint for consistent code standards

## Quick Start

### Prerequisites

- Python 3.12+
- Docker and Docker Compose
- PostgreSQL (or use Docker container)

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/codenamemomi/KANEC_backend
   cd KANEC_backend
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.sample .env
   ```

   Configure the following in your `.env` file:
   ```env
   # Database Configuration
   DB_HOST=localhost
   DB_PORT=5432
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_NAME=kanec_db

   # JWT Configuration
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60

   # Hedera Configuration
   HEDERA_NETWORK=testnet
   HEDERA_OPERATOR_ID=your-hedera-account-id
   HEDERA_OPERATOR_KEY=your-hedera-private-key
   PRIVATE_KEY_ENCRYPTION_KEY=your-32-character-encryption-key

   # Email Configuration (choose one)
   BREVO_API_KEY=your-brevo-api-key
   # OR
   MAIL_FROM=your-email@example.com
   MAIL_FROM_NAME=Kanec API

   # Redis Configuration
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   REDIS_PASSWORD=your-redis-password

   # Celery Configuration
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0

   # CORS Origins
   BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   ```

### Database Setup

1. **Create PostgreSQL database**
   ```sql
   CREATE USER kanec_user WITH PASSWORD 'your_password';
   CREATE DATABASE kanec_db;
   GRANT ALL PRIVILEGES ON DATABASE kanec_db TO kanec_user;
   ```

2. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

3. **Seed the database (optional)**
   ```bash
   python scripts/seed.py
   ```

### Running the Application

#### Development Mode
```bash
python main.py
```
The API will be available at `http://localhost:8000` with root path `/kanec`

#### Using Docker Compose (Development)
```bash
docker-compose up --build
```
The API will be available at `http://localhost:7006`

#### Using Docker Compose (Staging)
```bash
docker-compose -f docker-compose.staging.yml up --build
```

#### Using Docker Compose (Production)
```bash
docker-compose -f docker-compose.prod.yml up --build
```

#### Using Docker (Standalone)
```bash
docker build -t kanec-api .
docker run -p 7001:7001 --env-file .env kanec-api
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/` (returns `{"status": "ok"}`)

## AI_Analytics Features

The platform provides comprehensive analytics capabilities powered by AI and machine learning:

### User Insights
- **Personalized Analytics**: Category distribution, donation frequency trends, and impact scores
- **ML-Powered Recommendations**: Project suggestions based on donation history and preferences using collaborative filtering
- **User Impact Scoring**: Multi-factor scoring system with levels (Beginner to Champion)
- **Comparative Analysis**: User percentile ranking among all donors

### Platform Analytics
- **Global Statistics**: Total donations, amount raised, projects, and donors
- **Category Analytics**: Top categories by funding with detailed breakdowns and growth metrics
- **Project Analytics**: Individual project performance metrics and completion tracking
- **Real-time Activity**: Recent donations and project creation statistics

### Data-Driven Features
- **Trend Analysis**: Monthly donation patterns and growth metrics using time-series analysis
- **Predictive Insights**: Donation frequency predictions and category growth analysis
- **Smart Recommendations**: Content-based and collaborative filtering for project suggestions

## API Endpoints

### Authentication & User Management
- `POST /api/v1/auth/register` - Register new user with email verification
- `POST /api/v1/auth/login` - User login (OAuth2 password flow)
- `POST /api/v1/auth/login_swagger` - Login via Swagger UI
- `GET /api/v1/auth/me` - Get current user details
- `GET /api/v1/auth/profile` - Get user profile with wallet balance
- `PUT /api/v1/auth/profile` - Update user profile
- `PATCH /api/v1/auth/profile` - Partially update user profile
- `POST /api/v1/auth/change-password` - Change user password
- `DELETE /api/v1/auth/account` - Delete user account
- `GET /api/v1/auth/export-wallet` - Export encrypted private key (advanced users)
- `POST /api/v1/auth/verify-email` - Verify email with OTP
- `POST /api/v1/auth/resend-verification` - Resend email verification OTP
- `GET /api/v1/auth/verification-status` - Check email verification status
- `POST /api/v1/auth/forgot-password` - Request password reset OTP
- `POST /api/v1/auth/reset-password` - Reset password with OTP

### Projects
- `POST /api/v1/projects/` - Create project (admin/org only)
- `POST /api/v1/projects/{project_id}/image` - Upload project image
- `GET /api/v1/projects/` - Get all verified projects
- `GET /api/v1/projects/{project_id}` - Get project details
- `GET /api/v1/projects/{project_id}/transparency` - Get project transparency data
- `PATCH /api/v1/projects/{project_id}/verify` - Verify project (admin only)

### Donations
- `POST /api/v1/donations/` - Make HBAR donation from user wallet to project
- `GET /api/v1/donations/my-donations` - Get user's completed donations with project details

### P2P Transfers
- `POST /api/v1/p2p/transfer` - Transfer HBAR between user wallets with memo support
- `GET /api/v1/p2p/balance` - Get user HBAR balance
- `POST /api/v1/p2p/validate-wallet` - Validate wallet address format and existence

### Transaction Tracing
- `GET /api/v1/trace/trace/{tx_hash}` - Trace donation transaction on Hedera Mirror Node

### AI Analytics
- `GET /api/v1/analytics/user/insights` - Get ML-powered user donation insights and personalized recommendations
- `GET /api/v1/analytics/global/stats` - Get global platform donation statistics
- `GET /api/v1/analytics/platform/overview` - Get comprehensive platform analytics with category breakdowns
- `GET /api/v1/analytics/project/{project_id}` - Get detailed analytics for a specific project
- `GET /api/v1/analytics/categories/top` - Get top categories by total funding
- `GET /api/v1/analytics/user/compare` - Compare user donation behavior with platform averages

## User Roles & Permissions

- **Donor**: Can view projects, make donations, access P2P transfers, view personal analytics, manage profile
- **Organization (Org)**: All donor permissions + create/manage projects, upload project images
- **Admin**: All permissions + verify projects, access all analytics, manage platform settings

## P2P Transfers

The platform supports direct HBAR transfers between users:

### Features
- **Secure Transfers**: Encrypted private key handling with balance validation
- **Memo Support**: Add transaction memos for transfer tracking
- **Balance Checking**: Real-time balance verification before transfers
- **Wallet Validation**: Validate recipient wallet addresses
- **Transfer Limits**: Maximum 10,000 HBAR per transfer for security

### Transfer Process
1. User initiates transfer with recipient wallet, amount, and optional memo
2. System validates sender balance, recipient wallet format, and transfer limits (max 10,000 HBAR)
3. Transaction is submitted to Hedera network with memo support
4. Transfer status is tracked and confirmed via transaction hash

## Profile Management

### Features
- **Profile Updates**: Full profile information management
- **Password Security**: Secure password changes with validation
- **Wallet Balance**: Real-time HBAR balance display
- **Account Deletion**: Complete account removal with data cleanup
- **Email Verification**: OTP-based email verification system

### Security Features
- **Private Key Encryption**: AES encryption for stored private keys
- **JWT Authentication**: Secure token-based authentication
- **Rate Limiting**: API rate limiting to prevent abuse
- **Input Validation**: Comprehensive input sanitization

## Email & OTP Verification

### Features
- **Email Verification**: OTP-based email verification for new accounts
- **Password Reset**: Secure password reset with OTP codes
- **Multiple Providers**: Support for Brevo and SendGrid email services
- **OTP Management**: Secure OTP generation and validation
- **Resend Functionality**: Ability to resend verification codes

### Verification Process
1. User registers or requests password reset
2. OTP code sent to email address
3. User enters OTP for verification
4. Account activated or password reset completed

## Hedera Integration

The platform integrates with Hedera network for:
- **Wallet Creation**: Automatic Hedera account creation for new projects
- **HBAR Transfers**: Secure donation processing
- **Transaction Verification**: Mirror node integration for transaction validation
- **Transaction Tracing**: Complete donation history tracking

### Hedera Configuration

Ensure your `.env` file includes valid Hedera credentials:
- `HEDERA_NETWORK`: `testnet` or `mainnet`
- `HEDERA_OPERATOR_ID`: Your Hedera account ID (format: 0.0.xxxxx)
- `HEDERA_OPERATOR_KEY`: Your Hedera private key (ECDSA format)
- `PRIVATE_KEY_ENCRYPTION_KEY`: 32-character key for encrypting user private keys using Fernet

### Email Configuration

Choose one email provider:
- **Brevo**: Set `BREVO_API_KEY` for Brevo/SendGrid integration
- **SMTP**: Set `MAIL_FROM` and `MAIL_FROM_NAME` for custom SMTP

### Redis Configuration

Required for Celery and rate limiting:
- `REDIS_HOST`: Redis server hostname
- `REDIS_PORT`: Redis server port (default: 6379)
- `REDIS_DB`: Redis database number
- `REDIS_PASSWORD`: Redis password (if required)

## Database Models

### User
- Basic user information (name, email, role)
- Role-based permissions (donor/admin/org) with enum validation
- Hedera wallet address and encrypted ECDSA private key
- Email verification status and OTP management
- Profile management with timestamps (created_at, updated_at)

### Project
- Project details (title, description, category, location)
- Fundraising goals (target_amount) and amount_raised tracking
- HBAR wallet address for donations (auto-generated)
- Verification status and admin approval workflow
- Image upload support with file path storage
- Organization ownership with foreign key relationship
- Backers count tracking

### Donation
- Donation records with HBAR amounts and transaction hashes
- Hedera transaction hashes for verification (unique constraint)
- Status tracking (pending/completed/failed) with enum
- Foreign key relationships to donor (User) and project
- Timestamp tracking (created_at, updated_at)

### Organization
- Organization profile (name, contact_email, region)
- Verification status for project creation permissions
- Admin approval workflow
- Foreign key relationship to creator (User)

## Testing

Run the complete test suite:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=api --cov-report=html
```

Run specific test files:
```bash
pytest tests/v1/auth/test_signup.py
pytest tests/v1/analytics/test_analytics_summary.py
```

Run tests with async support:
```bash
pytest -v --asyncio-mode=auto
```

### Test Categories
- **Authentication**: User registration, login, JWT tokens
- **Projects**: CRUD operations, image uploads, verification
- **Donations**: HBAR transfers, transaction validation
- **Analytics**: AI insights, ML recommendations, statistics
- **P2P Transfers**: Wallet validation, balance checking
- **Email/OTP**: Verification codes, password reset

## Database Migrations

### Create new migration
```bash
alembic revision --autogenerate -m "migration description"
```

### Apply migrations
```bash
alembic upgrade head
```

### Downgrade
```bash
alembic downgrade -1
```

## Deployment

### Production Docker Setup
```bash
docker-compose -f docker-compose.prod.yml up --build
```

### Environment Variables for Production
Ensure all required environment variables are set in your production environment, including:
- Database credentials
- Hedera network configuration
- JWT secret keys
- CORS origins

## Development Workflow

### Code Quality
```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .
pylint api/

# Type checking (if configured)
mypy api/
```

### Pre-commit Hooks
```bash
pre-commit install
pre-commit run --all-files
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Set up development environment with Docker:
   ```bash
   docker-compose up -d db redis
   pip install -r requirements.txt
   ```
4. Make your changes following the code quality standards
5. Add comprehensive tests for new features
6. Ensure all tests pass: `pytest --cov=api --cov-report=html`
7. Update documentation if needed
8. Commit your changes (`git commit -m 'Add amazing feature'`)
9. Push to the branch (`git push origin feature/amazing-feature`)
10. Open a Pull Request

### Code Standards
- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **pylint**: Static analysis
- **pytest**: Testing with async support
- **pre-commit**: Automated code quality checks

## License

This project is licensed under the terms specified in the LICENSE file.

## Support

For support and questions, please open an issue on the GitHub repository.
