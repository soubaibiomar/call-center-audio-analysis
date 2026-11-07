import type { ModelVersionPage } from "../../lib/api/generated";
import { useApiQuery } from "../../lib/api/queries";
import { ReportWorkspace } from "../workspace/ReportWorkspace";
import {
    Empty,
    Heading,
    Pending,
    QueryProblem,
    Status,
} from "../workspace/shared";

export function ModelsPage() {
    const models = useApiQuery<ModelVersionPage>(
        "/api/v1/model-versions?limit=100&offset=0",
        "ModelVersionPage",
    );
    return (
        <>
            <Heading title="Model lab">
                Inspect registered versions and recorded inference receipts.
            </Heading>
            <div className="data-notice">
                <strong>Training and promotion controls are unavailable</strong>
                <span>
                    This page does not start training, change defaults or claim
                    that a candidate improved.
                </span>
            </div>
            {models.isError ? (
                <QueryProblem error={models.error} retry={models.refetch} />
            ) : !models.data ? (
                <Pending />
            ) : models.data.items.length ? (
                <section className="panel calls-panel">
                    <h2>Registered model versions (latest 100)</h2>
                    <div className="table-scroll">
                        <table>
                            <caption className="sr-only">
                                Tenant model registry; artifact locations are
                                not exposed
                            </caption>
                            <thead>
                                <tr>
                                    <th>Family</th>
                                    <th>Version</th>
                                    <th>Status</th>
                                    <th>Registered</th>
                                </tr>
                            </thead>
                            <tbody>
                                {models.data.items.map((model) => (
                                    <tr key={model.id}>
                                        <th scope="row">{model.family}</th>
                                        <td>{model.version}</td>
                                        <td>
                                            <Status value={model.status} />
                                        </td>
                                        <td>
                                            {new Date(
                                                model.created_at,
                                            ).toLocaleString()}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </section>
            ) : (
                <Empty title="No registered model versions">
                    Report receipts may still exist. No registry status is
                    inferred from cached model files.
                </Empty>
            )}
            <ReportWorkspace kind="receipts" />
        </>
    );
}
