# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is an **Office Automation System (办公辅助系统)** built with Python, featuring a hybrid desktop application using pywebview for the frontend and Python for backend automation. The system primarily focuses on WeChat automation, task scheduling, and office workflow management.

## Key Technologies

- **Backend**: Python 3.x with SQLite database
- **Frontend**: Vue 3 + Element Plus + Animate.css (CDN-based, no build tools)
- **Desktop GUI**: pywebview for native desktop integration
- **Automation**: wxauto, uiautomation, pyautogui for WeChat automation
- **Task Scheduling**: APScheduler for background task management
- **Notifications**: win10toast for Windows system notifications

## Core Build Commands

### Dependencies Management
```powershell
# Install full dependencies (development)
pip install -r requirements.txt

# Install minimal dependencies (for lightweight builds)
pip install -r requirements_minimal.txt
```

### Building Executables

```powershell
# Standard build (20-30MB)
python build_clean.py

# Minimal build (15-25MB) - Ultra-lightweight
python build_minimal.py

# Compatible build
python build_compatible.py

# Simple build
python build_simple.py

# Lean build
python build_lean.py
```

### Development Commands

```powershell
# Run the application
python main.py

# Test database operations
python demo_room_data_query.py

# Test task system
python demo_task_system.py

# Check system status
python check_status.py

# Verify retry tasks
python verify_retry.py
```

## Architecture Overview

### Core Application Structure

The application follows a **modular hybrid architecture** with clear separation between frontend, backend, and automation components:

1. **Main Entry Point** (`main.py`): Initializes database, task manager, and launches the pywebview interface
2. **API Layer** (`apis.py`): Bridges frontend JavaScript calls with Python backend functions
3. **Database Layer** (`sqlite3_util.py`): Handles all SQLite operations with proper abstraction
4. **Task Management** (`task_manager.py`): APScheduler-based background task system
5. **Automation Engine** (`wechat_automation.py`): WeChat UI automation using multiple libraries
6. **Web Interface** (`web/`): Vue 3 frontend with Element Plus components

### Database Schema

The system uses SQLite with the following key tables:
- `users` - User management and import tracking
- `rooms` - WeChat live room information
- `time_of_live` - Scheduled live broadcast times
- `tasks` - APScheduler task management
- `wechat_phrases` - Common phrases for automation
- `products` & `images` - Product and image management

### Task Management System

**Background Task Architecture**:
- **APScheduler** manages all scheduled operations
- **Persistent Storage** in SQLite for task recovery after restarts
- **Windows Notifications** for user alerts
- **Automatic Cleanup** of expired tasks

Key task types:
- `live_reminder` - WeChat live broadcast reminders
- `follow_task` - Automated following operations
- `retry_task` - Failed operation retry mechanisms

### WeChat Automation Pipeline

1. **Window Detection** - Locates WeChat application windows
2. **UI Element Recognition** - Uses uiautomation + template matching
3. **Action Execution** - Simulates human-like interactions
4. **State Management** - Tracks operation progress and handles failures
5. **Retry Logic** - Configurable retry mechanisms for failed operations

## Configuration Management

### System Configuration (`config.json`)
- **Intervals**: Timing controls for various operations
- **Retry Logic**: Maximum attempts and backoff strategies  
- **Features**: Toggle switches for optional functionality
- **Timeouts**: Operation timeout settings

### Build Configuration
- **Standard Build**: Full functionality (~20-30MB)
- **Minimal Build**: Core features only (~15-25MB)
- **Clean Builds**: Automatic cleanup and optimization

## Development Guidelines

### Code Architecture Rules
- **Frontend**: Use CDN dependencies only (no build tools/npm)
- **Animation**: Use animate.css classes, avoid custom animations
- **Error Handling**: Comprehensive try-catch with user-friendly messages
- **Logging**: Structured logging with progress tracking

### Module Dependencies
- Core modules can function independently with graceful degradation
- Optional features (screenshots, notifications) fail silently if dependencies missing
- Database operations are atomic with proper rollback handling

### Build Optimization
The build system uses advanced PyInstaller optimization:
- **Module Exclusion**: Removes unused heavy libraries (numpy, opencv, etc.)
- **Binary Filtering**: Excludes unnecessary system DLLs
- **Spec Files**: Custom PyInstaller specifications for size optimization
- **Virtual Environment**: Isolated build environments for consistency

### Testing Strategy
- **Unit Tests**: Database operations and core functions
- **Integration Tests**: API endpoints and task scheduling
- **Build Tests**: Verify executable functionality across Windows versions
- **Cleanup**: Automatic test artifact removal

## Common Development Tasks

### Adding New Automation Features
1. Implement core logic in appropriate module (e.g., `wechat_automation.py`)
2. Add API endpoints in `apis.py` 
3. Create database tables/queries in `sqlite3_util.py` if needed
4. Add frontend components in `web/pages/`
5. Update configuration in `config.json` if required

### Database Schema Changes
1. Update table creation functions in `sqlite3_util.py`
2. Add migration logic for existing installations
3. Update API functions that interact with new schema
4. Test with both fresh installations and upgrades

### Task Scheduling Updates
1. Add task types in `task_manager.py`
2. Create global execution functions (avoid serialization issues)
3. Update task loading logic in `_load_existing_tasks`
4. Add API endpoints for task management

## Build Optimization Notes

- **Target Size**: 15-25MB for minimal builds, 20-30MB for standard
- **Startup Performance**: ~2-3 seconds on modern systems
- **Memory Usage**: Optimized for low memory footprint
- **Compatibility**: Windows 10/11 with .NET Framework 4.7.2+

The build system automatically handles dependency optimization, file exclusion, and size minimization while maintaining full functionality.
