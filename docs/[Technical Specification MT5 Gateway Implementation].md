  
[Technical Specification: MT5 Gateway Implementation]  
1. Project Context  
 * Project Name: MT5-CRS (Algorithmic Trading System).  
 * Current Environment: Windows Server 2022 (172.19.141.255).  
 * Objective: Implement the MT5Service class to handle connections to the local MetaTrader 5 terminal.  
2. Development Workflow (Mandatory)  
We utilize a Strict TDD (Test-Driven Development) Workflow with a local CI runner.  
 * The Runner: gemini_review_bridge.py is our local CI/CD enforcement script.  
 * The Rule: You MUST NOT execute git commit directly. Instead, you must run python3 gemini_review_bridge.py.  
   * Why? This script automatically locates a validation script, runs it, and only commits if the validation passes. This ensures code quality.  
 * The Validator: For every feature, you must create a specific validation script named scripts/audit_current_task.py.  
3. Task Assignment: Task #014.1 - Core MT5 Service  
Step A: Review Standards  
 * Read scripts/audit_template.py. This file contains the required structure and helper functions for our validation scripts.  
Step B: Implementation (src/gateway/mt5_service.py)  
 * Requirement: Create a singleton class MT5Service.  
 * Configuration: Use dotenv to load MT5_PATH, MT5_LOGIN, MT5_PASSWORD, MT5_SERVER from environment variables.  
 * Method: Implement connect().  
   * Constraint: You MUST use mt5.initialize(path=...) using the path from env vars (essential for our portable setup).  
 * Method: Implement is_connected() -> bool.  
Step C: Validation Setup (scripts/audit_current_task.py)  
 * Create this file strictly following the pattern in scripts/audit_template.py.  
 * Assertions Required:  
   * File src/gateway/mt5_service.py exists.  
   * File contains keyword "MetaTrader5".  
   * File contains keyword "path=" (verifying portable path support).  
   * File contains keyword "class MT5Service".  
Step D: Execution Loop  
 * Generate the code for Step B and Step C.  
 * Execute: python3 gemini_review_bridge.py  
 * Refine: If the bridge reports an error (Exit Code 1), fix your code and re-run the bridge.  
 * Complete: The task is done when the bridge successfully commits the code (Exit Code 0).  
Action:  
Start Step A and proceed through the loop.  
