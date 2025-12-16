---
description: Comprehensive eMMA software analysis with improvement recommendations
argument-hint: [component]
---

# Deep Analysis & Improvement Command for eMMA

You are analyzing the eMMA (Enterprise Monitoring & Management Application) project. Use all available skills and the EMMA_PROJECT_CONTEXT.md as your reference.

## Analysis Target
Component to analyze: $ARGUMENTS

Available targets:
- `full-stack` - Complete application analysis (default)
- `backend` - FastAPI backend only
- `frontend` - React frontend only
- `agents` - Monitoring agents
- `infrastructure` - Docker, CI/CD, deployment
- `security` - Security audit across all components

## Analysis Framework

### Phase 1: Project Context Review
1. Read and apply EMMA_PROJECT_CONTEXT.md standards
2. Understand current architecture and tech stack
3. Review recent changes (git log)

### Phase 2: Component Analysis

Analyze the specified component across these dimensions:

#### A. Functionality & Features
- Current feature completeness
- Missing critical features from roadmap
- Feature gaps compared to monitoring best practices
- User experience improvements

#### B. Code Quality & Standards
- Adherence to EMMA_PROJECT_CONTEXT.md standards
- Code organization and modularity
- Type hints coverage (Python)
- TypeScript usage (React)
- Documentation completeness

#### C. Testing Coverage
**Use api-testing and webapp-testing skills**
- Current test coverage percentage
- Missing test scenarios
- Integration test gaps
- E2E test coverage for critical flows
- Generate missing tests using skills

#### D. Security Analysis
- Authentication/Authorization review
- JWT implementation audit
- Input validation coverage
- SQL injection prevention
- CORS configuration
- Secret management
- Dependency vulnerabilities

#### E. Performance & Scalability
- Database query optimization
- API endpoint performance
- WebSocket connection handling
- Memory usage patterns
- Docker image optimization
- Frontend bundle size

#### F. Architecture & Design
- Adherence to documented architecture
- Separation of concerns
- Dependency management
- Error handling patterns
- Logging and monitoring

### Phase 3: Improvement Recommendations

For each finding, provide:

1. **Issue Description**: Clear explanation of the problem
2. **Impact Level**: Critical / High / Medium / Low
3. **Effort Estimate**: Small / Medium / Large
4. **Priority Score**: (Impact x Feasibility)
5. **Actionable Solution**: Specific code changes or implementations
6. **Code Example**: Show before/after when applicable

### Phase 4: Test Generation

**Automatically generate missing tests:**
- Use `api-testing` skill for API tests
- Use `webapp-testing` skill for React tests
- Generate pytest files for backend
- Generate Vitest files for frontend

### Phase 5: Implementation Roadmap

Create a prioritized roadmap:

**Quick Wins (This Week)**:
- High impact, low effort improvements
- Critical security fixes
- Simple refactoring

**Strategic Improvements (This Month)**:
- Medium/high impact features
- Architecture improvements
- Performance optimizations

**Long-term Enhancements (This Quarter)**:
- Major features from backlog
- Scalability improvements
- Infrastructure upgrades

## Special Focus Areas for eMMA

### Backend (FastAPI)
- JWT refresh token security
- WebSocket reconnection handling
- Agent communication reliability
- Service health check accuracy
- Database query performance
- Alembic migration safety

### Frontend (React)
- Real-time update rendering
- WebSocket state management
- Error boundary implementation
- Loading state handling
- Dashboard performance
- Mobile responsiveness

### Agents
- Heartbeat reliability
- Multi-protocol monitoring
- Error recovery
- Resource usage
- Configuration management

### Infrastructure
- Docker build optimization
- GitHub Actions efficiency
- Database backup strategy
- Secrets management
- Health check robustness

## Analysis Execution

Now, execute the analysis for the specified component.

1. Read EMMA_PROJECT_CONTEXT.md for standards
2. Scan relevant directories
3. Apply analysis framework
4. Generate tests using skills
5. Create prioritized recommendations
6. Output comprehensive report

**Start analysis now and provide actionable improvements!**
