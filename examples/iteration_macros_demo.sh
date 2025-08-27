#!/usr/bin/env argorator

# LOG_FILE (file): Application log file to analyze
# SERVER_LIST (str): Comma-separated list of servers  
# CONFIG_PATHS (str): Colon-separated configuration paths
# OUTPUT_DIR (str): Directory for generated reports

echo "🔄 ARGORATOR ITERATION MACROS - FEATURE SHOWCASE"
echo "==============================================="
echo ""

echo "📊 1. FILE LINE ITERATION (Type-based detection)"
echo "   Processing log file line by line..."

# for line in $LOG_FILE
echo "   📄 $line"

echo ""
echo "🖥️  2. DELIMITED DATA PROCESSING (CSV-style)"
echo "   Processing comma-separated server list..."

# for server in $SERVER_LIST sep ,
echo "   🖥️  Server: $server"

echo ""
echo "⚙️  3. PATH-STYLE ITERATION (Colon-separated)"
echo "   Scanning configuration paths..."

# for config_path in $CONFIG_PATHS separated by :
echo "   📁 Config path: $config_path"

echo ""
echo "📁 4. PATTERN MATCHING"
echo "   Finding configuration files..."

# for config_file in /tmp/config*/*.conf
echo "   📄 Found: $config_file"

echo ""
echo "📊 5. RANGE ITERATION"
echo "   Generating sequential reports..."

# for num in {1..3}
echo "   📝 Generating report #$num"

echo ""
echo "🔧 6. FUNCTION-BASED PROCESSING"
echo "   Advanced server monitoring..."

# for server in $SERVER_LIST sep , | with $OUTPUT_DIR
monitor_server() {
    local hostname="$1"
    local output_dir="$2"
    
    echo "   🔍 Monitoring: $hostname"
    echo "   💾 Saving results to: $output_dir"
    
    # Simulate monitoring
    status=$((RANDOM % 2))
    if [ $status -eq 0 ]; then
        echo "   ✅ $hostname is healthy"
    else
        echo "   ⚠️  $hostname needs attention"
    fi
}

echo ""
echo "✨ FEATURES DEMONSTRATED:"
echo "  🔄 Automatic type detection (file vs array)"
echo "  📝 Multiple separator formats (, and :)"
echo "  📁 File pattern matching (*.conf)"
echo "  📊 Numeric ranges ({1..3})"
echo "  🔧 Function parameter passing"
echo "  🎯 Clean, readable syntax"
echo ""
echo "🎉 All iteration types working seamlessly!"
echo "   No manual bash loop syntax required!"