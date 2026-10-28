"use client";

import {
  createWatch,
  deleteAccount,
  forgetAccountReport,
  getAlerts,
  getWatches,
  listAccountReports,
  removeWatch,
  saveAccountReports,
} from "@/lib/api";
import { bridgeToken } from "@/lib/bridgeSession";
import { clearAccountData } from "@/lib/accountData";

export async function accountReports() {
  return listAccountReports(await bridgeToken());
}

export async function saveToAccount(ids: string[]) {
  return saveAccountReports(await bridgeToken(), ids);
}

export async function forgetFromAccount(id: string) {
  return forgetAccountReport(await bridgeToken(), id);
}

export async function myAlerts() {
  return getAlerts(await bridgeToken());
}

export async function myWatches() {
  return getWatches(await bridgeToken());
}

export async function watchProject(project: Parameters<typeof createWatch>[1], language: "en" | "hi") {
  return createWatch(await bridgeToken(), project, language);
}

export async function stopWatching(watchId: string) {
  return removeWatch(await bridgeToken(), watchId);
}

export async function deleteMyData() {
  await deleteAccount(await bridgeToken());
  clearAccountData();
}
