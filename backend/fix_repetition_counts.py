#!/usr/bin/env python3
"""
Fix repetition counts for existing analyses
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import connect_to_mongo
from app.models.documents import AnalysisDoc, WordEventDoc
from app.services.scoring import recompute_counts
from loguru import logger

async def fix_repetition_counts():
    """Fix repetition counts for all analyses"""
    await connect_to_mongo()
    
    # Get all analyses
    analyses = await AnalysisDoc.find_all().to_list()
    logger.info(f"Found {len(analyses)} analyses to fix")
    
    for analysis in analyses:
        try:
            # Get word events for this analysis
            word_events = await WordEventDoc.find({"analysis_id": analysis.id}).to_list()
            logger.info(f"Analysis {analysis.id}: {len(word_events)} word events")
            
            if not word_events:
                logger.warning(f"No word events found for analysis {analysis.id}")
                continue
            
            # Recompute counts with repetition
            counts = recompute_counts(word_events)
            logger.info(f"Recomputed counts: {counts}")
            
            # Update analysis summary
            if not analysis.summary:
                analysis.summary = {}
            
            analysis.summary["counts"] = counts
            
            # Save updated analysis
            await analysis.save()
            logger.info(f"Updated analysis {analysis.id}")
            
        except Exception as e:
            logger.error(f"Error processing analysis {analysis.id}: {e}")
            continue
    
    logger.info("Finished fixing repetition counts")

if __name__ == "__main__":
    asyncio.run(fix_repetition_counts())

