#!/bin/bash
"""
Advanced Steganography Suite - Quick Launcher
===========================================

This script provides easy shortcuts to launch the application in different modes.
"""

# Default: Start GUI
if [ "$#" -eq 0 ]; then
    echo "🚀 Starting Advanced Steganography Suite GUI..."
    python3 run_app.py --mode gui
    exit 0
fi

# Parse arguments
case "$1" in
    "gui"|"GUI")
        echo "🚀 Starting GUI mode..."
        python3 run_app.py --mode gui
        ;;
    "cli"|"CLI")
        echo "🚀 Starting CLI mode..."
        python3 run_app.py --mode cli
        ;;
    "api"|"API")
        echo "🚀 Starting API server..."
        python3 run_app.py --mode api
        ;;
    "demo"|"DEMO")
        echo "🚀 Running demo..."
        python3 demo.py
        ;;
    "test"|"TEST")
        echo "🚀 Running tests..."
        python3 test_app.py
        ;;
    "help"|"HELP"|"-h"|"--help")
        echo "Advanced Steganography Suite v2.0"
        echo "=================================="
        echo ""
        echo "Usage: $0 [mode]"
        echo ""
        echo "Modes:"
        echo "  gui    - Start graphical user interface (default)"
        echo "  cli    - Start command-line interface"
        echo "  api    - Start REST API server"
        echo "  demo   - Run demonstration"
        echo "  test   - Run test suite"
        echo "  help   - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0           # Start GUI (default)"
        echo "  $0 gui       # Start GUI explicitly"
        echo "  $0 cli       # Start CLI mode"
        echo "  $0 api       # Start API server"
        echo "  $0 demo      # Run demo"
        ;;
    *)
        echo "❌ Unknown mode: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
