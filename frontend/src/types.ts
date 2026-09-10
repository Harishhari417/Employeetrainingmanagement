export type Role = "HR_ADMIN" | "MANAGER" | "EMPLOYEE";

export type RatingLabel = "Poor" | "Fair" | "Good" | "V Good" | "Excellent";

export interface FeedbackFormData {
  programme: string;
  participantName: string;
  designation: string;
  location: string;
  dates: string;
  trainer: string;
  ratings: Record<string, RatingLabel | "">;
  knowledgeBefore: number | null;
  knowledgeAfter: number | null;
  bestModule: string;
  missedModule: string;
  majorLearning: string;
  ideasToImplement: string;
  remarks: string;
}

export interface AttendanceRow {
  employeeId: string;
  employeeName: string;
  department: string;
  attendance: "Present" | "Absent" | "Partial";
  feedbackStatus: "Pending" | "Submitted" | "Not Applicable";
}
