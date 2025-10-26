=======
# Kanec API

A FastAPI-based donation platform that enables cryptocurrency donations using Hedera HBAR tokens. The platform allows organizations to create donation projects, users to make donations, and provides transparent transaction tracking through Hedera's distributed ledger.

## Features

- **User Management**: Role-based authentication (Donor, Admin, Organization)
- **Project Management**: Create and manage donation projects with HBAR targets
- **HBAR Donations**: Secure cryptocurrency donations via Hedera network
- **Wallet Integration**: Automatic Hedera wallet creation for projects
- **Transaction Tracing**: Verify and track donation transactions on Hedera
- **Organization Support**: Organization accounts for managing multiple projects
- **PostgreSQL Database**: Robust data storage with SQLAlchemy ORM
- **Docker Support**: Containerized deployment with Docker Compose

## Technology Stack

- **Backend**: FastAPI (Python 3.12)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Blockchain**: Hedera SDK for HBAR transactions
- **Migration**: Alembic for database schema management
- **Authentication**: JWT tokens with role-based access control
- **Containerization**: Docker & Docker Compose

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
The API will be available at `http://localhost:8000`

#### Using Docker Compose
```bash
docker-compose up --build
```
The API will be available at `http://localhost:7006`

#### Using Docker (Production)
```bash
docker build -t kanec-api .
docker run -p 7001:7001 --env-file .env kanec-api
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/` (returns `{"status": "ok"}`)

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login (OAuth2 password flow)

### Projects
- `POST /api/v1/projects/` - Create project (admin/org only)
- `GET /api/v1/projects/` - Get all verified projects
- `GET /api/v1/projects/{project_id}` - Get project details
- `GET /api/v1/projects/{project_id}/transparency` - Get project transparency data
- `PATCH /api/v1/projects/{project_id}/verify` - Verify project (admin only)

### Donations
- `POST /api/v1/donations/` - Make HBAR donation

### Transaction Tracing
- `GET /api/v1/trace/trace/{tx_hash}` - Trace donation transaction

## User Roles

- **Donor**: Can view projects and make donations
- **Organization (Org)**: Can create and manage projects
- **Admin**: Full access including project verification

## Hedera Integration

The platform integrates with Hedera network for:
- **Wallet Creation**: Automatic Hedera account creation for new projects
- **HBAR Transfers**: Secure donation processing
- **Transaction Verification**: Mirror node integration for transaction validation
- **Transaction Tracing**: Complete donation history tracking

### Hedera Configuration

Ensure your `.env` file includes valid Hedera credentials:
- `HEDERA_NETWORK`: `testnet` or `mainnet`
- `HEDERA_OPERATOR_ID`: Your Hedera account ID
- `HEDERA_OPERATOR_KEY`: Your Hedera private key

## Database Models

### User
- Basic user information
- Role-based permissions (donor/admin/org)
- Wallet address for donations

### Project
- Project details and fundraising goals
- HBAR wallet address
- Verification status
- Amount raised tracking

### Donation
- Donation records with transaction hashes
- Status tracking (pending/completed/failed)
- Links to donor and project

### Organization
- Organization management
- Contact information
- Verification status

## Testing

Run the test suite:
```bash
pytest
```

Run specific test files:
```bash
python -m unittest tests/v1/auth/test_login.py
```

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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the terms specified in the LICENSE file.

## Support

For support and questions, please open an issue on the GitHub repository.
