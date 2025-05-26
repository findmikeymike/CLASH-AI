import { createClient } from "@supabase/supabase-js";

// Initialize Supabase client
const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
);

/**
 * Get the current user ID (authenticated or anonymous)
 */
export const getUserId = async (): Promise<string> => {
  // Check for authenticated user
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (session?.user?.id) {
    return session.user.id;
  }

  // Use anonymous ID from localStorage
  let anonymousId = localStorage.getItem("anonymousUserId");
  if (!anonymousId) {
    anonymousId = `anon_${Math.random().toString(36).substring(2, 15)}`;
    localStorage.setItem("anonymousUserId", anonymousId);
  }

  return anonymousId;
};

/**
 * Get the user's remaining minutes
 */
export const getUserMinutes = async (): Promise<number> => {
  try {
    const userId = await getUserId();

    const { data, error } = await supabase.functions.invoke(
      "supabase-functions-user-minutes",
      {
        body: { userId },
        method: "GET",
      },
    );

    if (error) {
      console.error("Error fetching user minutes:", error);
      return 0;
    }

    return data?.remainingMinutes || 0;
  } catch (error) {
    console.error("Error in getUserMinutes:", error);
    return 0;
  }
};

/**
 * Update the user's minutes (add or use)
 */
export const updateUserMinutes = async (options: {
  minutesUsed?: number;
  minutesAdded?: number;
}): Promise<number> => {
  try {
    const userId = await getUserId();
    const { minutesUsed, minutesAdded } = options;

    const { data, error } = await supabase.functions.invoke(
      "supabase-functions-user-minutes",
      {
        body: { userId, minutesUsed, minutesAdded },
        method: "POST",
      },
    );

    if (error) {
      console.error("Error updating user minutes:", error);
      return 0;
    }

    return data?.remainingMinutes || 0;
  } catch (error) {
    console.error("Error in updateUserMinutes:", error);
    return 0;
  }
};
