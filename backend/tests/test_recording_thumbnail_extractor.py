"""Tests for RecordingThumbnailExtractor."""

import unittest
from backend.services.media.recording_thumbnail_extractor import (
    RecordingThumbnailExtractor,
    ThumbnailFormat,
    ThumbnailQuality,
)


class TestRecordingThumbnailExtractor(unittest.TestCase):

    def setUp(self):
        self.extractor = RecordingThumbnailExtractor(
            output_base_dir="/tmp/elviq/thumbnails",
            default_interval=10.0,
            default_quality=ThumbnailQuality.MEDIUM,
            default_format=ThumbnailFormat.JPEG,
        )

    def test_submit_extraction_basic(self):
        job = self.extractor.submit_extraction(
            recording_id="rec_001",
            source_path="/recordings/meeting_001.mp4",
            duration_seconds=60.0,
        )
        self.assertIsNotNone(job)
        self.assertEqual(job.status, "completed")
        self.assertEqual(job.recording_id, "rec_001")

    def test_thumbnails_generated(self):
        job = self.extractor.submit_extraction(
            recording_id="rec_002",
            source_path="/recordings/meeting_002.mp4",
            duration_seconds=90.0,
            interval_seconds=10.0,
        )
        self.assertGreater(len(job.thumbnails), 0)

    def test_thumbnail_count(self):
        job = self.extractor.submit_extraction(
            recording_id="rec_003",
            source_path="/recordings/meeting_003.mp4",
            duration_seconds=30.0,
            interval_seconds=10.0,
        )
        # 30s / 10s = 3 frames expected
        self.assertEqual(len(job.thumbnails), 3)

    def test_thumbnail_dimensions_medium(self):
        job = self.extractor.submit_extraction(
            recording_id="rec_004",
            source_path="/path/to/rec.mp4",
            duration_seconds=20.0,
            quality=ThumbnailQuality.MEDIUM,
        )
        for thumb in job.thumbnails:
            self.assertEqual(thumb.width, 320)
            self.assertEqual(thumb.height, 180)

    def test_thumbnail_dimensions_high(self):
        job = self.extractor.submit_extraction(
            recording_id="rec_005",
            source_path="/path/to/rec.mp4",
            duration_seconds=20.0,
            quality=ThumbnailQuality.HIGH,
        )
        for thumb in job.thumbnails:
            self.assertEqual(thumb.width, 640)
            self.assertEqual(thumb.height, 360)

    def test_cover_thumbnail_set(self):
        job = self.extractor.submit_extraction(
            recording_id="rec_006",
            source_path="/path.mp4",
            duration_seconds=40.0,
            interval_seconds=10.0,
        )
        cover = self.extractor.get_cover_thumbnail("rec_006")
        self.assertIsNotNone(cover)
        self.assertTrue(cover.is_cover)

    def test_get_thumbnails_sorted(self):
        self.extractor.submit_extraction(
            recording_id="rec_007",
            source_path="/path.mp4",
            duration_seconds=50.0,
            interval_seconds=10.0,
        )
        thumbs = self.extractor.get_thumbnails("rec_007")
        timestamps = [t.timestamp_ms for t in thumbs]
        self.assertEqual(timestamps, sorted(timestamps))

    def test_thumbnail_checksum_populated(self):
        job = self.extractor.submit_extraction(
            recording_id="rec_008",
            source_path="/path.mp4",
            duration_seconds=20.0,
        )
        for thumb in job.thumbnails:
            self.assertIsInstance(thumb.checksum_md5, str)
            self.assertGreater(len(thumb.checksum_md5), 0)

    def test_thumbnail_to_dict(self):
        job = self.extractor.submit_extraction(
            recording_id="rec_009",
            source_path="/path.mp4",
            duration_seconds=15.0,
        )
        thumb = job.thumbnails[0]
        d = thumb.to_dict()
        self.assertIn("thumbnail_id", d)
        self.assertIn("timestamp_ms", d)
        self.assertIn("file_path", d)

    def test_generate_thumbnail_strip(self):
        self.extractor.submit_extraction(
            recording_id="rec_010",
            source_path="/path.mp4",
            duration_seconds=100.0,
            interval_seconds=10.0,
        )
        strip = self.extractor.generate_thumbnail_strip("rec_010")
        self.assertIsNotNone(strip)
        self.assertGreater(strip.total_thumbnails, 0)
        self.assertGreater(strip.strip_width, 0)
        self.assertGreater(strip.strip_height, 0)

    def test_generate_vtt_content(self):
        self.extractor.submit_extraction(
            recording_id="rec_011",
            source_path="/path.mp4",
            duration_seconds=30.0,
            interval_seconds=10.0,
        )
        strip = self.extractor.generate_thumbnail_strip("rec_011")
        vtt = self.extractor.generate_vtt_content(strip)
        self.assertIn("WEBVTT", vtt)
        self.assertIn("-->", vtt)
        self.assertIn("#xywh=", vtt)

    def test_get_job(self):
        job = self.extractor.submit_extraction(
            recording_id="rec_012",
            source_path="/path.mp4",
            duration_seconds=20.0,
        )
        fetched = self.extractor.get_job(job.job_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.recording_id, "rec_012")

    def test_different_formats(self):
        for fmt in [ThumbnailFormat.JPEG, ThumbnailFormat.PNG, ThumbnailFormat.WEBP]:
            job = self.extractor.submit_extraction(
                recording_id=f"rec_{fmt.value}",
                source_path="/path.mp4",
                duration_seconds=10.0,
                fmt=fmt,
            )
            for thumb in job.thumbnails:
                self.assertEqual(thumb.format, fmt)

    def test_stats(self):
        self.extractor.submit_extraction("rec_stat", "/path.mp4", 20.0)
        stats = self.extractor.stats()
        self.assertIn("total_jobs", stats)
        self.assertIn("total_thumbnails", stats)
        self.assertGreater(stats["total_jobs"], 0)

    def test_ms_to_vtt(self):
        vtt = RecordingThumbnailExtractor._ms_to_vtt(3661000)
        self.assertEqual(vtt, "01:01:01.000")


if __name__ == "__main__":
    unittest.main()
