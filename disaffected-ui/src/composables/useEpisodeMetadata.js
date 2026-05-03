import { ref } from 'vue';

/**
 * Composable for episode metadata fields.
 *
 * All refs returned here are auto-unwrapped when accessed via `this.*` in
 * Options API components that call this in setup().
 */
export function useEpisodeMetadata() {
  // --- Core episode fields ---
  const currentEpisodeNumber = ref('');
  const currentEpisodeSlug = ref('');
  const currentEpisodeTitle = ref('');
  const currentEpisodeSubtitle = ref('');
  const currentEpisodeGuest = ref('');
  const currentEpisodeDescription = ref('');
  const currentEpisodeTags = ref('');
  const currentEpisodeNotes = ref('');
  const currentEpisodeExplicit = ref(false);
  const currentEpisodeContentWarnings = ref('');
  const currentEpisodeRecordingDate = ref(null);
  const currentEpisodeProducer = ref('');
  const currentEpisodeEditor = ref('');
  const currentEpisodePublishStatus = ref('draft');
  const currentEpisodeScheduleDatetime = ref(null);
  const currentEpisodeVisibility = ref('public');

  // --- OmnyStudio ---
  const currentEpisodeOmnyDescription = ref('');
  const currentEpisodeOmnyVisibility = ref('public');
  const currentEpisodeOmnyPublishStatus = ref('draft');
  const currentEpisodeOmnyScheduleDatetime = ref(null);

  // --- YouTube ---
  const currentEpisodeYtTitle = ref('');
  const currentEpisodeYtDescription = ref('');
  const currentEpisodeYtTags = ref('');
  const currentEpisodeYtPrivacyStatus = ref('private');
  const currentEpisodeYtScheduleDatetime = ref(null);

  // --- Social media ---
  const currentEpisodeSocialHashtags = ref('');
  const currentEpisodeTwitterPostText = ref('');
  const currentEpisodeTwitterScheduleDatetime = ref(null);
  const currentEpisodeInstagramCaption = ref('');
  const currentEpisodeInstagramScheduleDatetime = ref(null);
  const currentEpisodeFacebookPostText = ref('');
  const currentEpisodeFacebookScheduleDatetime = ref(null);
  const currentEpisodeTiktokCaption = ref('');
  const currentEpisodeTiktokScheduleDatetime = ref(null);

  // --- Misc episode flags ---
  const currentEpisodeIsDummy = ref(false);

  // --- Air schedule ---
  const currentAirDate = ref('');
  const currentAirTime = ref('');
  const currentAirTimezone = ref('America/New_York');
  const currentShowTimezone = ref('America/New_York');

  // --- Production ---
  const currentProductionStatus = ref('draft');
  const productionStatuses = ref([
    { title: 'Scheduled', value: 'scheduled' },
    { title: 'Draft', value: 'draft' },
    { title: 'Production', value: 'production' },
    { title: 'Running', value: 'running' },
    { title: 'Completed', value: 'completed' }
  ]);

  /**
   * Reset all episode metadata fields to their default values.
   */
  function resetEpisodeMetadata() {
    currentEpisodeNumber.value = '';
    currentEpisodeSlug.value = '';
    currentEpisodeTitle.value = '';
    currentEpisodeSubtitle.value = '';
    currentEpisodeGuest.value = '';
    currentEpisodeDescription.value = '';
    currentEpisodeTags.value = '';
    currentEpisodeNotes.value = '';
    currentEpisodeExplicit.value = false;
    currentEpisodeContentWarnings.value = '';
    currentEpisodeRecordingDate.value = null;
    currentEpisodeProducer.value = '';
    currentEpisodeEditor.value = '';
    currentEpisodePublishStatus.value = 'draft';
    currentEpisodeScheduleDatetime.value = null;
    currentEpisodeVisibility.value = 'public';
    // OmnyStudio
    currentEpisodeOmnyDescription.value = '';
    currentEpisodeOmnyVisibility.value = 'public';
    currentEpisodeOmnyPublishStatus.value = 'draft';
    currentEpisodeOmnyScheduleDatetime.value = null;
    // YouTube
    currentEpisodeYtTitle.value = '';
    currentEpisodeYtDescription.value = '';
    currentEpisodeYtTags.value = '';
    currentEpisodeYtPrivacyStatus.value = 'private';
    currentEpisodeYtScheduleDatetime.value = null;
    // Social media
    currentEpisodeSocialHashtags.value = '';
    currentEpisodeTwitterPostText.value = '';
    currentEpisodeTwitterScheduleDatetime.value = null;
    currentEpisodeInstagramCaption.value = '';
    currentEpisodeInstagramScheduleDatetime.value = null;
    currentEpisodeFacebookPostText.value = '';
    currentEpisodeFacebookScheduleDatetime.value = null;
    currentEpisodeTiktokCaption.value = '';
    currentEpisodeTiktokScheduleDatetime.value = null;
    // Misc
    currentEpisodeIsDummy.value = false;
    // Air schedule
    currentAirDate.value = '';
    currentAirTime.value = '';
    currentAirTimezone.value = 'America/New_York';
    currentShowTimezone.value = 'America/New_York';
    // Production
    currentProductionStatus.value = 'draft';
  }

  /**
   * Populate all episode metadata fields from an API response object.
   * Expects the `info` object from the episode info endpoint.
   *
   * @param {Object} info - Episode info object from the API
   */
  function populateFromApiResponse(info) {
    if (!info) return;

    currentEpisodeSlug.value = info.slug || '';
    currentEpisodeTitle.value = info.title || '';
    currentEpisodeSubtitle.value = info.subtitle || '';
    currentEpisodeGuest.value = info.guest || '';
    currentEpisodeDescription.value = info.description || '';
    currentEpisodeTags.value = info.tags || '';
    currentEpisodeNotes.value = info.notes || '';
    currentEpisodeExplicit.value = info.explicit || false;
    currentEpisodeContentWarnings.value = info.content_warnings || '';
    currentEpisodeRecordingDate.value = info.recording_date || null;
    currentEpisodeProducer.value = info.producer || '';
    currentEpisodeEditor.value = info.editor || '';
    currentEpisodePublishStatus.value = info.publish_status || 'draft';
    currentEpisodeScheduleDatetime.value = info.schedule_datetime || null;
    currentEpisodeVisibility.value = info.visibility || 'public';
    // OmnyStudio
    currentEpisodeOmnyDescription.value = info.omny_description || '';
    currentEpisodeOmnyVisibility.value = info.omny_visibility || 'public';
    currentEpisodeOmnyPublishStatus.value = info.omny_publish_status || 'draft';
    currentEpisodeOmnyScheduleDatetime.value = info.omny_schedule_datetime || null;
    // YouTube
    currentEpisodeYtTitle.value = info.yt_title || '';
    currentEpisodeYtDescription.value = info.yt_description || '';
    currentEpisodeYtTags.value = info.yt_tags || '';
    currentEpisodeYtPrivacyStatus.value = info.yt_privacy_status || 'private';
    currentEpisodeYtScheduleDatetime.value = info.yt_schedule_datetime || null;
    // Social media
    currentEpisodeSocialHashtags.value = info.social_hashtags || '';
    currentEpisodeTwitterPostText.value = info.twitter_post_text || '';
    currentEpisodeTwitterScheduleDatetime.value = info.twitter_schedule_datetime || null;
    currentEpisodeInstagramCaption.value = info.instagram_caption || '';
    currentEpisodeInstagramScheduleDatetime.value = info.instagram_schedule_datetime || null;
    currentEpisodeFacebookPostText.value = info.facebook_post_text || '';
    currentEpisodeFacebookScheduleDatetime.value = info.facebook_schedule_datetime || null;
    currentEpisodeTiktokCaption.value = info.tiktok_caption || '';
    currentEpisodeTiktokScheduleDatetime.value = info.tiktok_schedule_datetime || null;
    // Misc
    currentEpisodeIsDummy.value = info.is_dummy || false;
    // Air schedule
    currentAirDate.value = info.airdate || '';
    currentAirTime.value = info.airtime || '';
    currentAirTimezone.value = info.airtimezone || 'America/New_York';
    currentShowTimezone.value = info.show_timezone || 'America/New_York';
    // Production
    currentProductionStatus.value = info.status || 'draft';
  }

  return {
    // Refs
    currentEpisodeNumber,
    currentEpisodeSlug,
    currentEpisodeTitle,
    currentEpisodeSubtitle,
    currentEpisodeGuest,
    currentEpisodeDescription,
    currentEpisodeTags,
    currentEpisodeNotes,
    currentEpisodeExplicit,
    currentEpisodeContentWarnings,
    currentEpisodeRecordingDate,
    currentEpisodeProducer,
    currentEpisodeEditor,
    currentEpisodePublishStatus,
    currentEpisodeScheduleDatetime,
    currentEpisodeVisibility,
    currentEpisodeOmnyDescription,
    currentEpisodeOmnyVisibility,
    currentEpisodeOmnyPublishStatus,
    currentEpisodeOmnyScheduleDatetime,
    currentEpisodeYtTitle,
    currentEpisodeYtDescription,
    currentEpisodeYtTags,
    currentEpisodeYtPrivacyStatus,
    currentEpisodeYtScheduleDatetime,
    currentEpisodeSocialHashtags,
    currentEpisodeTwitterPostText,
    currentEpisodeTwitterScheduleDatetime,
    currentEpisodeInstagramCaption,
    currentEpisodeInstagramScheduleDatetime,
    currentEpisodeFacebookPostText,
    currentEpisodeFacebookScheduleDatetime,
    currentEpisodeTiktokCaption,
    currentEpisodeTiktokScheduleDatetime,
    currentEpisodeIsDummy,
    currentAirDate,
    currentAirTime,
    currentAirTimezone,
    currentShowTimezone,
    currentProductionStatus,
    productionStatuses,
    // Methods
    resetEpisodeMetadata,
    populateFromApiResponse
  };
}
