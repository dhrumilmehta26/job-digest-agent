#!/usr/bin/env python3
"""
Entry point for Job Aggregator.

Usage:
    python run.py              # Run full aggregation pipeline
    python run.py --test       # Run with test mode (no email)
    python run.py --ui         # Start local UI server
    python run.py --export     # Export jobs to JSON only
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    parser = argparse.ArgumentParser(
        description='Job Aggregator - Fetch, store, and notify about job listings'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode (fetches jobs but does not send email)'
    )
    
    parser.add_argument(
        '--ui',
        action='store_true',
        help='Start the local UI server'
    )
    
    parser.add_argument(
        '--export',
        action='store_true',
        help='Export jobs to JSON file only (requires database connection)'
    )
    
    parser.add_argument(
        '--test-email',
        type=str,
        metavar='EMAIL',
        help='Send a test email to verify SMTP configuration'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show database statistics'
    )
    
    args = parser.parse_args()
    
    if args.ui:
        # Start UI server
        from api.server import run_server
        run_server()
        return
    
    if args.test_email:
        # Send test email
        from src.utils.config import Config
        from src.notifications.email_sender import EmailSender
        
        config = Config()
        sender = EmailSender(
            smtp_host=config.smtp_host,
            smtp_port=config.smtp_port,
            smtp_user=config.smtp_user,
            smtp_password=config.smtp_password,
            from_email=config.from_email,
            from_name=config.from_name,
            use_tls=config.smtp_use_tls
        )
        
        success = sender.send_test_email(args.test_email)
        sys.exit(0 if success else 1)
    
    if args.stats:
        # Show stats
        from src.utils.config import Config
        from src.database.connection import DatabaseConnection
        from src.database.operations import JobOperations
        
        config = Config()
        conn = DatabaseConnection(config.mongodb_uri, config.mongodb_database)
        db = conn.connect()
        ops = JobOperations(db)
        
        stats = ops.get_stats()
        print("\n📊 Database Statistics:")
        print(f"   Total jobs: {stats['total_jobs']}")
        print(f"   Jobs (24h): {stats['jobs_last_24h']}")
        print(f"   Jobs (48h): {stats['jobs_last_48h']}")
        print(f"   New jobs (24h): {stats['new_jobs_last_24h']}")
        print(f"\n   By source:")
        for source, count in stats['by_source'].items():
            print(f"      {source}: {count}")
        
        conn.disconnect()
        return
    
    if args.export:
        # Export only
        from src.main import JobAggregator
        
        aggregator = JobAggregator()
        if aggregator.setup():
            aggregator.export_jobs_json()
            aggregator.db_conn.disconnect()
        return
    
    # Run full pipeline
    from src.main import JobAggregator
    
    aggregator = JobAggregator()
    
    if args.test:
        # Test mode - fetch and store, but don't email
        print("🧪 Running in TEST mode (no email will be sent)")
        
        if not aggregator.setup():
            sys.exit(1)
        
        all_jobs = aggregator.fetch_all_jobs()
        filtered_jobs = aggregator.filter_jobs(all_jobs)
        new_count, _ = aggregator.store_jobs(filtered_jobs)
        
        print(f"\n✅ Test complete. Found {new_count} new jobs.")
        print("   Email notification was skipped (test mode)")
        
        aggregator.export_jobs_json()
        aggregator.db_conn.disconnect()
    else:
        # Full run
        success = aggregator.run()
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()



