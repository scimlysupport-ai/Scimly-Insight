export interface DashboardWidget {
  id: string | number;
  chartType: string;
  title: string;
  data: any;
  // The real interface is likely more complex,
  // but this is enough for the dashboard grid.
}