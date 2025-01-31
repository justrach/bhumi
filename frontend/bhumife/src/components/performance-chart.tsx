"use client"

import { Bar, BarChart, CartesianGrid, XAxis, YAxis, Cell, Tooltip } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartConfig, ChartContainer } from "@/components/ui/chart"

const chartData = [
  { client: "LiteLLM", speed: 13.79 },
  { client: "Native", speed: 5.55 },
  { client: "Bhumi", speed: 4.26 },
  { client: "GenAI", speed: 6.76 },
].sort((a, b) => b.speed - a.speed)

const chartConfig = {
  speed: {
    label: "Response Time (s)",
    color: "hsl(15,85%,70%)",
  },
} satisfies ChartConfig

export function PerformanceChart() {
  return (
    <Card className="border-2">
      <CardHeader>
        <CardTitle className="text-2xl">Performance Comparison</CardTitle>
        <CardDescription className="text-base">
          Response time comparison across different AI clients(Bhumi is 3.2x faster than alternatives)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig}>
          <BarChart
            data={chartData}
            height={300}
            margin={{
              left: 40,
              right: 12,
              top: 12,
              bottom: 12,
            }}
          >
            <CartesianGrid 
              horizontal={true}
              vertical={false} 
              strokeDasharray="3 3" 
              stroke="#f0f0f0"
            />
            <XAxis
              dataKey="client"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
            />
            <YAxis
              tickLine={false}
              axisLine={false}
              tickMargin={8}
            />
            <Tooltip
              cursor={{ fill: 'rgba(0, 0, 0, 0.05)' }}
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                return (
                  <div className="rounded-lg border bg-white px-3 py-2 shadow-sm">
                    <div className="grid grid-cols-2 gap-2">
                      <div className="flex flex-col">
                        <span className="text-[0.70rem] uppercase text-muted-foreground">
                          Client
                        </span>
                        <span className="font-bold text-sm">
                          {payload[0].payload.client}
                        </span>
                      </div>
                      <div className="flex flex-col">
                        <span className="text-[0.70rem] uppercase text-muted-foreground">
                          Response Time
                        </span>
                        <span className="font-bold text-sm">
                          {payload[0].value}s
                        </span>
                      </div>
                    </div>
                  </div>
                );
              }}
            />
            <Bar
              dataKey="speed"
              fill="hsl(15,85%,70%)"
              radius={[4, 4, 0, 0]}
              barSize={50}
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.client === "Bhumi" 
                    ? "hsl(15,85%,70%)" 
                    : "hsl(15,85%,70%, 0.6)"}
                />
              ))}
            </Bar>
          </BarChart>
        </ChartContainer>
      </CardContent>
      {/* <CardFooter className="border-t bg-slate-50">
        <div className="flex w-full items-start gap-2 text-sm">
          <div className="grid gap-2">
            <div className="flex items-center gap-2 font-medium leading-none text-lg">
              Bhumi is 3.2x faster than alternatives
              <TrendingUp className="h-5 w-5 text-[hsl(142,76%,36%)]" />
            </div>
            <div className="flex items-center gap-2 leading-none text-muted-foreground">
              Latest benchmark results - 2024
            </div>
          </div>
        </div>
      </CardFooter> */}
    </Card>
  )
} 