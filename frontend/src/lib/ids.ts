/** Check ids are 32 hex characters; anything else is a mistyped link, not worth asking the API. */
export const CHECK_ID_PATTERN = /^[0-9a-f]{32}$/;
