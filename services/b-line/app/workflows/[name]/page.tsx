"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ArrowLeft, Workflow, RefreshCw, ArrowRight } from "lucide-react";
import { api } from "@/lib/api/client";

interface WorkflowManifest {
  name: string;
  summary: string;
  author: string;
  state: string;
  version?: string;
  steps?: any[];
  triggers?: {
    event?: string;
    schedule?: string;
    webhook?: string;
  };
  environment?: {
    variables?: Record<string, string>;
  };
}

export default function WorkflowDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [workflow, setWorkflow] = useState<WorkflowManifest | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (params.name) {
      loadWorkflow(params.name as string);
    }
  }, [params.name]);

  const loadWorkflow = async (name: string) => {
    try {
      const data = await api.manifests.getWorkflow(name);
      setWorkflow(data);
    } catch (error) {
      console.error("Failed to load workflow:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!workflow) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold">Workflow not found</h2>
          <Button className="mt-4" onClick={() => router.push("/workflows")}>
            Back to Workflows
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      
      <div className="flex flex-1 flex-col">
        <Header />
        
        <main className="flex-1 overflow-y-auto bg-background p-6">
          <div className="max-w-5xl mx-auto space-y-6">
            {/* Back Button */}
            <Button variant="ghost" onClick={() => router.push("/workflows")}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Workflows
            </Button>

            {/* Workflow Header */}
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <Workflow className="h-10 w-10 text-primary" />
                  <div>
                    <h1 className="text-3xl font-bold tracking-tight">{workflow.name}</h1>
                    {workflow.version && (
                      <p className="text-sm text-muted-foreground">v{workflow.version}</p>
                    )}
                  </div>
                </div>
                <p className="text-lg text-muted-foreground">{workflow.summary}</p>
              </div>
              <div className="flex gap-2">
                <Badge variant={workflow.state === "stable" ? "default" : "secondary"} className="text-sm">
                  {workflow.state}
                </Badge>
              </div>
            </div>

            <Separator />

            {/* Details Grid */}
            <div className="grid gap-6 md:grid-cols-2">
              {/* Basic Info */}
              <Card>
                <CardHeader>
                  <CardTitle>Basic Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <div className="text-sm font-medium">Author</div>
                    <div className="text-sm text-muted-foreground">{workflow.author || "Unknown"}</div>
                  </div>
                  <div>
                    <div className="text-sm font-medium">State</div>
                    <div className="text-sm text-muted-foreground capitalize">{workflow.state}</div>
                  </div>
                  {workflow.version && (
                    <div>
                      <div className="text-sm font-medium">Version</div>
                      <div className="text-sm text-muted-foreground">{workflow.version}</div>
                    </div>
                  )}
                  {workflow.steps && (
                    <div>
                      <div className="text-sm font-medium">Total Steps</div>
                      <div className="text-sm text-muted-foreground">{workflow.steps.length}</div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Triggers */}
              {workflow.triggers && (
                <Card>
                  <CardHeader>
                    <CardTitle>Triggers</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {workflow.triggers.event && (
                      <div>
                        <div className="text-sm font-medium">Event</div>
                        <div className="text-sm text-muted-foreground">{workflow.triggers.event}</div>
                      </div>
                    )}
                    {workflow.triggers.schedule && (
                      <div>
                        <div className="text-sm font-medium">Schedule</div>
                        <div className="text-sm text-muted-foreground font-mono">{workflow.triggers.schedule}</div>
                      </div>
                    )}
                    {workflow.triggers.webhook && (
                      <div>
                        <div className="text-sm font-medium">Webhook</div>
                        <div className="text-sm text-muted-foreground font-mono text-xs">
                          {workflow.triggers.webhook}
                        </div>
                      </div>
                    )}
                    {!workflow.triggers.event && !workflow.triggers.schedule && !workflow.triggers.webhook && (
                      <div className="text-sm text-muted-foreground">Manual execution only</div>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Workflow Steps */}
            {workflow.steps && workflow.steps.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Workflow Steps</CardTitle>
                  <CardDescription>Sequential execution steps in this workflow</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {workflow.steps.map((step: any, index: number) => (
                      <div key={index} className="flex items-start gap-4">
                        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-semibold text-sm">
                          {index + 1}
                        </div>
                        <div className="flex-1 border-l-2 border-primary/20 pl-4 pb-4">
                          <div className="font-medium">{step.name || `Step ${index + 1}`}</div>
                          {step.description && (
                            <div className="text-sm text-muted-foreground mt-1">{step.description}</div>
                          )}
                          {step.type && (
                            <Badge variant="outline" className="mt-2">{step.type}</Badge>
                          )}
                          {step.action && (
                            <div className="mt-2 text-xs text-muted-foreground">
                              Action: <code className="px-1 py-0.5 bg-muted rounded">{step.action}</code>
                            </div>
                          )}
                        </div>
                        {index < (workflow.steps?.length || 0) - 1 && (
                          <ArrowRight className="h-4 w-4 text-muted-foreground mt-2" />
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Environment Variables */}
            {workflow.environment?.variables && Object.keys(workflow.environment.variables).length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Environment Variables</CardTitle>
                  <CardDescription>Configuration variables for this workflow</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {Object.entries(workflow.environment.variables).map(([key, value]) => (
                      <div key={key} className="flex justify-between items-center p-2 bg-muted/50 rounded">
                        <code className="text-sm font-semibold">{key}</code>
                        <code className="text-sm text-muted-foreground">{value}</code>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Actions</CardTitle>
              </CardHeader>
              <CardContent className="flex gap-2">
                <Button disabled title="Coming soon">
                  Execute Workflow
                </Button>
                <Button variant="outline" disabled title="Coming soon">
                  Edit Manifest
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => loadWorkflow(params.name as string)}
                >
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Refresh
                </Button>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
}
